#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Adapted from https://github.com/bluesky-social/cookbook/blob/main/python-bsky-post/create_bsky_post.py

import os
import sys
import json
import re
from argparse import ArgumentParser as ArgParser
from typing import Dict, List
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from pullmetadata import PodcastMetadata

__version__ = '1.0.0'
debug:bool = False
configfile:str = ""
inputfile:str = ""
title:str = ""
episode:int = 0
podcasturl:str = ""
useragent:str = "MostlySecurityBot/1.0 (https://mostlysecurity.com/; podcast@mostlysecurity.com)"


class BlueskyPostBot:
    def __init__(self, configfile):
        self.configfile = configfile

    def bsky_login_session(self, pds_url: str, handle: str, password: str) -> Dict:
        resp = requests.post(
            pds_url + "/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
        )
        resp.raise_for_status()
        return resp.json()


    def parse_mentions(self, text: str) -> List[Dict]:
        spans = []
        # regex based on: https://atproto.com/specs/handle#handle-identifier-syntax
        mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(mention_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "handle": m.group(1)[1:].decode("UTF-8"),
                }
            )
        return spans


    def parse_urls(self, text: str) -> List[Dict]:
        spans = []
        # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
        # tweaked to disallow some training punctuation
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(url_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "url": m.group(1).decode("UTF-8"),
                }
            )
        return spans


    def parse_facets(self, pds_url: str, text: str) -> List[Dict]:
        """
        parses post text and returns a list of app.bsky.richtext.facet objects for any mentions (@handle.example.com) or URLs (https://example.com)

        indexing must work with UTF-8 encoded bytestring offsets, not regular unicode string offsets, to match Bluesky API expectations
        """
        facets = []
        for m in self.parse_mentions(text):
            resp = requests.get(
                pds_url + "/xrpc/com.atproto.identity.resolveHandle",
                params={"handle": m["handle"]},
            )
            # if handle couldn't be resolved, just skip it! will be text in the post
            if resp.status_code == 400:
                continue
            did = resp.json()["did"]
            facets.append(
                {
                    "index": {
                        "byteStart": m["start"],
                        "byteEnd": m["end"],
                    },
                    "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
                }
            )
        for u in self.parse_urls(text):
            facets.append(
                {
                    "index": {
                        "byteStart": u["start"],
                        "byteEnd": u["end"],
                    },
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#link",
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )
        return facets


    def parse_uri(self, uri: str) -> Dict:
        if uri.startswith("at://"):
            repo, collection, rkey = uri.split("/")[2:5]
            return {"repo": repo, "collection": collection, "rkey": rkey}
        elif uri.startswith("https://bsky.app/"):
            repo, collection, rkey = uri.split("/")[4:7]
            if collection == "post":
                collection = "app.bsky.feed.post"
            elif collection == "lists":
                collection = "app.bsky.graph.list"
            elif collection == "feed":
                collection = "app.bsky.feed.generator"
            return {"repo": repo, "collection": collection, "rkey": rkey}
        else:
            raise Exception("unhandled URI format: " + uri)


    def get_reply_refs(self, pds_url: str, parent_uri: str) -> Dict:
        uri_parts = self.parse_uri(parent_uri)
        resp = requests.get(
            pds_url + "/xrpc/com.atproto.repo.getRecord",
            params=uri_parts,
        )
        resp.raise_for_status()
        parent = resp.json()
        root = parent
        parent_reply = parent["value"].get("reply")
        if parent_reply is not None:
            root_uri = parent_reply["root"]["uri"]
            root_repo, root_collection, root_rkey = root_uri.split("/")[2:5]
            resp = requests.get(
                pds_url + "/xrpc/com.atproto.repo.getRecord",
                params={
                    "repo": root_repo,
                    "collection": root_collection,
                    "rkey": root_rkey,
                },
            )
            resp.raise_for_status()
            root = resp.json()

        return {
            "root": {
                "uri": root["uri"],
                "cid": root["cid"],
            },
            "parent": {
                "uri": parent["uri"],
                "cid": parent["cid"],
            },
        }


    def upload_file(self, pds_url, access_token, filename, img_bytes) -> Dict:
        suffix = filename.split(".")[-1].lower()
        mimetype = "application/octet-stream"
        if suffix in ["png"]:
            mimetype = "image/png"
        elif suffix in ["jpeg", "jpg"]:
            mimetype = "image/jpeg"
        elif suffix in ["webp"]:
            mimetype = "image/webp"

        # WARNING: a non-naive implementation would strip EXIF metadata from JPEG files here by default
        resp = requests.post(
            pds_url + "/xrpc/com.atproto.repo.uploadBlob",
            headers={
                "Content-Type": mimetype,
                "Authorization": "Bearer " + access_token,
            },
            data=img_bytes,
        )
        resp.raise_for_status()
        return resp.json()["blob"]


    def upload_images(self, pds_url: str, access_token: str, image_paths: List[str], alt_text: str ) -> Dict:
        images = []
        for ip in image_paths:
            with open(ip, "rb") as f:
                img_bytes = f.read()
            # this size limit specified in the app.bsky.embed.images lexicon
            if len(img_bytes) > 1000000:
                raise Exception(
                    f"image file size too large. 1000000 bytes maximum, got: {len(img_bytes)}"
                )
            blob = self.upload_file(pds_url, access_token, ip, img_bytes)
            images.append({"alt": alt_text or "", "image": blob})
        return {
            "$type": "app.bsky.embed.images",
            "images": images,
        }


    def fetch_embed_url_card(self, pds_url: str, access_token: str, url: str) -> Dict:
        # the required fields for an embed card
        card = {
            "uri": url,
            "title": "",
            "description": "",
        }

        # fetch the HTML
        headers = {"User-Agent": useragent}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            card["title"] = title_tag["content"]

        description_tag = soup.find("meta", property="og:description")
        if description_tag:
            card["description"] = description_tag["content"]

        image_tag = soup.find("meta", property="og:image")
        if image_tag:
            img_url = image_tag["content"]
            if "://" not in img_url:
                img_url = url + img_url
            resp = requests.get(img_url, headers=headers)
            resp.raise_for_status()
            card["thumb"] = self.upload_file(pds_url, access_token, img_url, resp.content)

        return {
            "$type": "app.bsky.embed.external",
            "external": card,
        }


    def get_embed_ref(self, pds_url: str, ref_uri: str) -> Dict:
        uri_parts = self.parse_uri(ref_uri)
        resp = requests.get(
            pds_url + "/xrpc/com.atproto.repo.getRecord",
            params=uri_parts,
        )
        print(resp.json())
        resp.raise_for_status()
        record = resp.json()

        return {
            "$type": "app.bsky.embed.record",
            "record": {
                "uri": record["uri"],
                "cid": record["cid"],
            },
        }


    def create_post(self, text, link=None):
        load_dotenv(self.configfile, override=True)
        pds_url=os.environ.get("ATP_PDS_HOST") or "https://bsky.social"
        handle=os.environ.get("ATP_AUTH_HANDLE")
        password=os.environ.get("ATP_AUTH_PASSWORD")
        if len(handle) <= 0 or len(password) <= 0:
            print(f"Need handle and password")
            return 

        session = self.bsky_login_session(pds_url, handle, password)

        # trailing "Z" is preferred over "+00:00"
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # these are the required fields which every post must include
        post = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now,
        }

        # parse out mentions and URLs as "facets"
        if len(text) > 0:
            facets = self.parse_facets(pds_url, post["text"])
            if facets:
                post["facets"] = facets

        if link:
            try: 
                post["embed"] = self.fetch_embed_url_card(pds_url, session["accessJwt"], link)
            except Exception as e:
                print(f"embed: {e}")
                post["text"] = f"{text} - {link}"
                if len(post["text"]) > 0:
                    facets = self.parse_facets(pds_url, post["text"])
                    if facets:
                        post["facets"] = facets

        print("creating post:", file=sys.stderr)
        print(json.dumps(post, indent=2), file=sys.stderr)

        resp = requests.post(
            pds_url + "/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"], 'User-Agent': useragent},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )

        if resp.status_code != 200:
            post["text"] = f"{text} - {link}"
            if len(post["text"]) > 0:
                facets = self.parse_facets(pds_url, post["text"])
                if facets:
                    post["facets"] = facets
            resp = requests.post(
                pds_url + "/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": "Bearer " + session["accessJwt"], 'User-Agent': useragent},
                json={
                    "repo": session["did"],
                    "collection": "app.bsky.feed.post",
                    "record": post,
                },
            )
            print(f"createRecord response {resp.status_code}:", file=sys.stderr)
            print(json.dumps(resp.json(), indent=2))
            resp.raise_for_status()
        else:
            print("createRecord response:", file=sys.stderr)
            print(json.dumps(resp.json(), indent=2))
            resp.raise_for_status()

# def parseCommandLine_old():
#     parser = ArgParser(description="bsky.app post upload example script")
#     parser.add_argument(
#         "--pds-url", default=os.environ.get("ATP_PDS_HOST") or "https://bsky.social"
#     )
#     parser.add_argument("--handle", default=os.environ.get("ATP_AUTH_HANDLE"))
#     parser.add_argument("--password", default=os.environ.get("ATP_AUTH_PASSWORD"))
#     parser.add_argument("text", default="")
#     parser.add_argument("--image", action="append")
#     parser.add_argument("--alt-text")
#     parser.add_argument("--lang", action="append")
#     parser.add_argument("--reply-to")
#     parser.add_argument("--embed-url")
#     parser.add_argument("--embed-ref")
#     args = parser.parse_args()
#     if not (args.handle and args.password):
#         print("both handle and password are required", file=sys.stderr)
#         sys.exit(-1)
#     if args.image and len(args.image) > 4:
#         print("at most 4 images per post", file=sys.stderr)
#         sys.exit(-1)

#     return args



def version():
    print("Version: {}".format(__version__))

def postToBsky(bskybot, text, url):
    if debug:
        print(f"Text: {text}")
        print(f"URL : {url}")
    else:
        bskybot.create_post(text, url)

def postMetadata(bskybot, metadata: dict):
    global title
    # Create Chapter Posts
    ctoc = metadata['CTOC']
    chap = metadata['CHAP']
    for i in ctoc:
        ch = chap[i]
        if ch.get('url'):
            postToBsky(bskybot, ch['text'], ch['url'])
    # Create podcast post
    if len(title) <= 0:
        title = metadata['TIT2']


def parseCommandLine():
    global debug, configfile, inputfile, title, episode, podcasturl
    description = (
            'Script to pull the metadata out of a Podcast '
            'and format it.\n'
            '---------------------------------------------'
            '-----------------------------\n'
            )
    parser = ArgParser(description=description)
    parser.add_argument('-v', '--version', action='store_true', help='Show version numbers and exit')
    parser.add_argument('-c', '--configfile', help='Config file, default config.env')
    parser.add_argument('-i', '--inputfile', help='Specify the podcast file to extract')
    parser.add_argument('-t', '--title', help='Podcast Title for posting')
    parser.add_argument('-e', '--episode', type=int, help='Episode number')
    parser.add_argument('-p', '--podcasturl', help='URL to podcast for posting to bluesky')
    parser.add_argument('-d', '--debug', action='store_true', help='Prints extra stuff to stdout')
    
    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options
    del options

    if args.version:
        version()
    
    if args.debug:
        debug = args.debug

    if args.configfile:
        configfile = args.configfile
    else:
        configfile = "config.env"

    if args.inputfile:
        inputfile = args.inputfile

    if args.title:
        title = args.title

    if args.episode:
        episode = args.episode

    if args.podcasturl:
        podcasturl = args.podcasturl


def main():
    try:
        parseCommandLine()
        bskybot = BlueskyPostBot(configfile)
        if inputfile:
            podcast = PodcastMetadata(inputfile)
            metadata = podcast.extractMetadata()
            postMetadata(bskybot, metadata)
        
        if len(title) <= 0:
            print(f"Missing title")
            raise SystemExit(-1)

        if podcasturl:
            post_title = title
            if episode > 0:
                if title.startswith(f"Episode {episode}:"):
                    post_title = title
                elif title.startswith(f"{episode}:"):
                    post_title = f"Episode {episode}: {title[4:].strip()}"
                else:
                    post_title = f"Episode {episode}: {title}"
            else:
                print(f"Missing episode number")
                raise SystemExit(-1)

            postToBsky(bskybot, post_title, podcasturl)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
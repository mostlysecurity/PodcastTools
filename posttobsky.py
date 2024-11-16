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
podcasturl:str = ""

def bsky_login_session(pds_url: str, handle: str, password: str) -> Dict:
    resp = requests.post(
        pds_url + "/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
    )
    resp.raise_for_status()
    return resp.json()


def parse_mentions(text: str) -> List[Dict]:
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


def parse_urls(text: str) -> List[Dict]:
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


def parse_facets(pds_url: str, text: str) -> List[Dict]:
    """
    parses post text and returns a list of app.bsky.richtext.facet objects for any mentions (@handle.example.com) or URLs (https://example.com)

    indexing must work with UTF-8 encoded bytestring offsets, not regular unicode string offsets, to match Bluesky API expectations
    """
    facets = []
    for m in parse_mentions(text):
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
    for u in parse_urls(text):
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


def parse_uri(uri: str) -> Dict:
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


def get_reply_refs(pds_url: str, parent_uri: str) -> Dict:
    uri_parts = parse_uri(parent_uri)
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


def upload_file(pds_url, access_token, filename, img_bytes) -> Dict:
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


def upload_images(
    pds_url: str, access_token: str, image_paths: List[str], alt_text: str
) -> Dict:
    images = []
    for ip in image_paths:
        with open(ip, "rb") as f:
            img_bytes = f.read()
        # this size limit specified in the app.bsky.embed.images lexicon
        if len(img_bytes) > 1000000:
            raise Exception(
                f"image file size too large. 1000000 bytes maximum, got: {len(img_bytes)}"
            )
        blob = upload_file(pds_url, access_token, ip, img_bytes)
        images.append({"alt": alt_text or "", "image": blob})
    return {
        "$type": "app.bsky.embed.images",
        "images": images,
    }


def fetch_embed_url_card(pds_url: str, access_token: str, url: str) -> Dict:
    # the required fields for an embed card
    card = {
        "uri": url,
        "title": "",
        "description": "",
    }

    # fetch the HTML
    headers = {"User-Agent": "MostlySecurityBot/1.0 (https://mostlysecurity.com/; podcast@mostlysecurity.com)"}
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
        card["thumb"] = upload_file(pds_url, access_token, img_url, resp.content)

    return {
        "$type": "app.bsky.embed.external",
        "external": card,
    }


def get_embed_ref(pds_url: str, ref_uri: str) -> Dict:
    uri_parts = parse_uri(ref_uri)
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


def create_post(text, link=None):
    load_dotenv(".config")
    pds_url=os.environ.get("ATP_PDS_HOST") or "https://bsky.social"
    handle=os.environ.get("ATP_AUTH_HANDLE")
    password=os.environ.get("ATP_AUTH_PASSWORD")

    session = bsky_login_session(pds_url, handle, password)

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
        facets = parse_facets(pds_url, post["text"])
        if facets:
            post["facets"] = facets

    if link:
        post["embed"] = fetch_embed_url_card(pds_url, session["accessJwt"], link)

    print("creating post:", file=sys.stderr)
    print(json.dumps(post, indent=2), file=sys.stderr)

    resp = requests.post(
        pds_url + "/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": "Bearer " + session["accessJwt"], 'User-Agent': 'MostlySecurityBot/1.0 (https://mostlysecurity.com/; podcast@mostlysecurity.com)'},
        json={
            "repo": session["did"],
            "collection": "app.bsky.feed.post",
            "record": post,
        },
    )
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

def createChapterPost(text:str, url:str):
    create_post(text, url)

def postMetadata(metadata: dict):
    # Create Chapter Posts
    ctoc = metadata['CTOC']
    chap = metadata['CHAP']
    for i in ctoc:
        ch = chap[i]
        if ch.get('url'):
            create_post(ch['text'], ch['url'])

    # Create podcast post
    title = metadata['TIT2']
    # desc = metadata['COMM']
    if podcasturl:
        create_post(title,podcasturl)

def parseCommandLine():
    global debug, podcasturl
    inputfile:str = ""
    description = (
            'Script to pull the metadata out of a Podcast '
            'and format it.\n'
            '---------------------------------------------'
            '-----------------------------\n'
            )
    parser = ArgParser(description=description)
    parser.add_argument('-v', '--version', action='store_true', help='Show version numbers and exit')
    parser.add_argument('-i', '--inputfile', help='Specify the podcast file to extract')
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

    if args.inputfile:
        inputfile = args.inputfile
    
    if args.podcasturl:
        podcasturl = args.podcasturl

    if inputfile == None or inputfile == '':
        print("inputfile cannot be empty")
        raise SystemExit(-1)

    podcast = PodcastMetadata(inputfile)
    metadata = podcast.extractMetadata()
    return metadata


def main():
    metadata = parseCommandLine()
    # print(metadata)
    postMetadata(metadata)
    # create_post(args)


if __name__ == "__main__":
    main()
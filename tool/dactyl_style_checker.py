#!/usr/bin/env python3

###############################################################################
## Dactyl Style Police                                                       ##
## Author: Rome Reginelli                                                    ##
## Copyright: Ripple Labs, Inc. 2016                                         ##
##                                                                           ##
## Reads the markdown files to try and enforce elements of good style.       ##
###############################################################################

import logging
import argparse
#import nltk
import re
import collections
import yaml

from bs4 import BeautifulSoup

import dactyl_build

logger = logging.getLogger()

with open("word_substitutions.yaml", "r") as f:
	UNPLAIN_WORDS = yaml.load(f)
with open("phrase_substitutions.yaml", "r") as f:
	UNPLAIN_PHRASES = yaml.load(f)

def check_all_pages(target=None):
    """Reads all pages for a target and checks them for style."""
    target = dactyl_build.get_target(target)
    pages = dactyl_build.get_pages(target)

    pp_env = dactyl_build.setup_pp_env()

    style_issues = []
    for page in pages:
        if "md" not in page:
            # Not a doc page, move on
            continue
        logging.info("Checking page %s" % page["name"])
        page_issues = []
        html = dactyl_build.parse_markdown(page, pages=pages, target=target)
        soup = BeautifulSoup(html, "html.parser")

        content_elements = ["p","li","h1","h2","h3","h4","h5","h6"]
        passages = []
        for el in soup.find_all(content_elements):
            for passage in el.stripped_strings:
                passage_issues = check_passage(passage)
                if passage_issues:
                    page_issues += passage_issues

        if page_issues:
            style_issues.append( (page["name"], page_issues) )

    return style_issues

def check_passage(passage):
    """Checks an individual string of text for style issues."""
    issues = []
    logging.debug("Checking passage %s" % passage)
    #tokens = nltk.word_tokenize(passage)
    tokens = re.split(r"\s+", passage)
    for t in tokens:
        logging.debug
        if t.lower() in UNPLAIN_WORDS:
            issues.append( ("Unplain Word", t) )

    for phrase,sub in UNPLAIN_PHRASES.items():
        if phrase in passage.lower():
            #logging.warn("Unplain phrase: %s; suggest %s instead" % (phrase, sub))
            issues.append( ("Unplain Phrase", phrase) )

    return issues

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check content files for style issues.")
    parser.add_argument("--config", "-c", type=str,
        help="Specify path to an alternate config file.")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress status messages")
    cli_args = parser.parse_args()

    if not cli_args.quiet:
        logging.basicConfig(level=logging.INFO)

    if cli_args.config:
        dactyl_build.load_config(cli_args.config)
    else:
        dactyl_build.load_config()

    issues = check_all_pages()
    if issues:
        num_issues = sum(len(p[1]) for p in issues)
        print("Found %d issues:" % num_issues)
        for pagename,issuelist in issues:
            print("Page: %s" % pagename)
            c = collections.Counter(issuelist)
            for i, count_i in c.items():
                if i[0]=="Unplain Phrase":
                    print("   Discouraged phrase: %s (%d instances); suggest ''%s' instead." %
                                    ( i[1], count_i, UNPLAIN_PHRASES[i[1].lower()] ))
                elif i[0]=="Unplain Word":
                    print("   Discouraged word: %s (%d instances); suggest ''%s' instead." %
                                    ( i[1], count_i, UNPLAIN_WORDS[i[1].lower()] ))
                else:
                    print("   %s: %s (%d instances)" % (i[0], i[1], count_i))
        exit(1)
    else:
        print("Style check passed with flying colors!")
        exit(0)

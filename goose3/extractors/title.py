# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import re

from rdflib import URIRef

from goose3.constants import SCHEMA_ORG_NS
from goose3.extractors import BaseExtractor


TITLE_SPLITTERS = ["|", "-", "»", ":"]


class TitleExtractor(BaseExtractor):

    def clean_title(self, title):
        """Clean title with the use of og:site_name
        in this case try to get rid of site name
        and use TITLE_SPLITTERS to reformat title
        """
        # check if we have the site name in opengraph data
        ogp_site_name = URIRef("http://ogp.me/ns#site_name")
        if (None, ogp_site_name, None) in self.article.opengraph:
            site_name = self.article.opengraph.value(subject=URIRef(""), predicate=ogp_site_name)
            # remove the site name from title
            title = title.replace(str(site_name), '').strip()
        elif self.article.schema:
            for (_, _, o) in self.article.schema.triples((None, SCHEMA_ORG_NS.publisher, None)):
                for name in self.article.schema.objects(o, SCHEMA_ORG_NS.name):
                    title = title.replace(str(name), '').strip()
                    break

        # try to remove the domain from url
        if self.article.domain:
            pattern = re.compile(self.article.domain, re.IGNORECASE)
            title = pattern.sub("", title).strip()

        # split the title in words
        # TechCrunch | my wonderfull article
        # my wonderfull article | TechCrunch
        title_words = title.split()

        # check if first letter is in TITLE_SPLITTERS
        # if so remove it
        if title_words and title_words[0] in TITLE_SPLITTERS:
            title_words.pop(0)

        # check for a title that is empty or consists of only a
        # title splitter to avoid a IndexError below
        if not title_words:
            return ""

        # check if last letter is in TITLE_SPLITTERS
        # if so remove it
        if title_words[-1] in TITLE_SPLITTERS:
            title_words.pop(-1)

        # rebuild the title
        title = " ".join(title_words).strip()

        return title

    def get_title(self):
        """\
        Fetch the article title and analyze it
        """
        title = ''

        ogp_title = URIRef("http://ogp.me/ns#title")
        # rely on opengraph in case we have the data
        if (None, ogp_title, None) in self.article.opengraph:
            return self.clean_title(str(self.article.opengraph.value(subject=URIRef(""),
                                                                     predicate=ogp_title)))
        if self.article.schema:
            for (s, p, _) in self.article.schema.triples((None, SCHEMA_ORG_NS.headline, None)):
                v = self.article.schema.value(subject=s, predicate=p)
                if v:
                    return self.clean_title(str(v))

        # try to fetch the meta headline
        meta_headline = self.parser.getElementsByTag(self.article.doc,
                                                     tag="meta",
                                                     attr="name",
                                                     value="headline")
        if meta_headline is not None and len(meta_headline) > 0:
            title = self.parser.getAttribute(meta_headline[0], 'content')
            return self.clean_title(title)

        # otherwise use the title meta
        title_element = self.parser.getElementsByTag(self.article.doc, tag='title')
        if title_element is not None and len(title_element) > 0:
            title = self.parser.getText(title_element[0])
            return self.clean_title(title)

        return title

    def extract(self):
        return self.get_title()

#!/usr/bin/local/python
# encoding: utf-8
import sys
import sqlite3
from collections import namedtuple

conn = sqlite3.connect("wnjpn.db")

Word = namedtuple('Word', 'wordid lang lemma pron pos')

def getWords(lemma):
  cur = conn.execute("select * from word where lemma=?", (lemma,))
  return [Word(*row) for row in cur]

def getWord(wordid):
  cur = conn.execute("select * from word where wordid=?", (wordid,))
  return Word(*cur.fetchone())

Sense = namedtuple('Sense', 'synset wordid lang rank lexid freq src')

def getSenses(word):
  cur = conn.execute("select * from sense where wordid=?", (word.wordid,))
  return [Sense(*row) for row in cur]

def getSense(synset, lang='jpn'):
  cur = conn.execute("select * from sense where synset=? and lang=?",
                     (synset,lang))
  row = cur.fetchone()
  return row and Sense(*row) or None

Synset = namedtuple('Synset', 'synset pos name src')

def getSynset(synset):
  cur = conn.execute("select * from synset where synset=?", (synset,))
  return Synset(*cur.fetchone())

SynLink = namedtuple('SynLink', 'synset1 synset2 link src')

def getSynLinks(sense, link):
  cur = conn.execute("select * from synlink where synset1=? and link=?",
                     (sense.synset, link))
  return [SynLink(*row) for row in cur]

def getSynLinksRecursive(senses, link, lang='jpn', _depth=0):
  for sense in senses:
    synLinks = getSynLinks(sense, link)
    if synLinks:
      print(''.join([' '*2*_depth,
                     getWord(sense.wordid).lemma,
                     ' ',
                     getSynset(sense.synset).name]))
    _senses = []
    for synLink in synLinks:
      sense = getSense(synLink.synset2, lang)
      if sense:
        _senses.append(sense)

    getSynLinksRecursive(_senses, link, lang, _depth+1)

def getWordsFromSynset(synset, lang):
  cur = conn.execute("select word.* from sense, word where synset=? and word.lang=? and sense.wordid = word.wordid;", (synset,lang))
  return [Word(*row) for row in cur]

def getWordsFromSenses(sense, lang):
  for s in sense:
    print(getSynset(s.synset).name)
    syns = getWordsFromSynset(s.synset, lang)
    for sy in syns:
      print('  ' + sy.lemma)


if __name__ == '__main__':
  if len(sys.argv)>=3:
    words = getWords(sys.argv[1].decode('utf-8'))
    if words:
      for w in words:
        sense = getSenses(w)
        link = len(sys.argv)>=3 and sys.argv[2] or 'hypo'
        lang = len(sys.argv)==4 and sys.argv[3] or 'jpn'
        if link == 'syns':
          getWordsFromSenses(sense, lang)
        else:
          getSynLinksRecursive(sense, link, lang)
    else:
      print("(nothing found)", file=sys.stderr)
  else:
    print("""usage: wn.py word link [lang]
    word
      word to investigate
    link
      syns - Synonyms
      hype - Hypernyms
      inst - Instances
      hypo - Hyponym
      hasi - Has Instance
      mero - Meronyms
      mmem - Meronyms --- Member
      msub - Meronyms --- Substance
      mprt - Meronyms --- Part
      holo - Holonyms
      hmem - Holonyms --- Member
      hsub - Holonyms --- Substance
      hprt - Holonyms -- Part
      attr - Attributes
      sim - Similar to
      entag - Entails
      causg - Causes
      dmncg - Domain --- Category
      dmnug - Domain --- Usage
      dmnrg - Domain --- Region
      dmtcg - In Domain --- Category
      dmtug - In Domain --- Usage
      dmtrg - In Domain --- Region
      antsg - Antonyms
    lang (default: jpn)
      jpn - Japanese
      eng - English
   """)

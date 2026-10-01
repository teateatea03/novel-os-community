#!/usr/bin/env python3
"""Low-risk manuscript metrics: length, dialogue share, repetitions and sentences."""
from __future__ import annotations
import argparse,json,re
from collections import Counter
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--file',required=True);p.add_argument('--top',type=int,default=12);a=p.parse_args();text=Path(a.file).read_text(encoding='utf-8',errors='replace')
 sentences=[x.strip() for x in re.split(r'[。！？!?]+',text) if x.strip()]; dialogue=''.join(re.findall(r'[「『“].*?[」』”]',text,re.S)); words=re.findall(r'[\u3400-\u9fff]|[A-Za-z]+',text); grams=Counter(''.join(words[i:i+4]) for i in range(max(0,len(words)-3)))
 report={'chars':len(text),'sentences':len(sentences),'mean_sentence_chars':round(sum(map(len,sentences))/max(1,len(sentences)),1),'dialogue_char_share':round(len(dialogue)/max(1,len(text)),3),'top_repeated_4grams':[{'gram':g,'count':n} for g,n in grams.most_common(a.top) if n>1],'meta_markers':re.findall(r'\[(?:TODO|TBD|INSERT|META)\]',text,re.I)}
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

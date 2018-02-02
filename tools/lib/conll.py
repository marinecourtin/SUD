#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2009-2018 Kim Gerdes
# kim AT gerdes. fr
# http://arborator.ilpga.fr/
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU Affero General Public License (the "License")
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# See the GNU General Public License (www.gnu.org) for more details.
#
# You can retrieve a copy of of version 3 of the GNU Affero General Public License
# from http://www.gnu.org/licenses/agpl-3.0.html 
####

import collections, re
#debug=False
debug=True


class Tree(dict):
	"""
	just a dictionary that maps nodenumber->{"t":"qsdf", ...}
	moreover: 
		sentencefeatures is a dictionary with sentence wide information, eg "comments":"comment line content"
			there is a special key: _comments used for comments that are not of the form x = yyy, they are stored as such
		words is not necessarily a list of tokens: it contains the actual correctly spelled words, ie. the hyphen (1-2) lines
	"""
	def __init__(self, *args, **kwargs):
		self.update(*args, **kwargs)
		self.sentencefeatures={}
		self.words=[]

	def __getitem__(self, key):
		val = dict.__getitem__(self, key)
		#print 'GET', key
		return val

	def __setitem__(self, key, val):
		#print 'SET', key, val
		dict.__setitem__(self, key, val)

	def __repr__(self):
		#dictrepr = dict.__repr__(self)
		#return '%s(%s)' % (type(self).__name__, dictrepr)
		return "\n".join(["Tree: "+self.sentence()]+[f+": "+v for f,v in self.sentencefeatures.items()]+[str(i)+": "+self[i].get("t","")+"\t"+str(self[i]) for i in self])
	
	def update(self, *args, **kwargs):
		#print 'update', args, kwargs
		for k, v in dict(*args, **kwargs).items():
			self[k] = v
	
	def sentence(self):
		if self.words==[]:
			self.words = [self[i].get("t","") for i in sorted(self)]
		return " ".join(self.words)
	
	def conllu(self):
		treestring = ""
		for stftkey in sorted(self.sentencefeatures):
			if stftkey=="_comments":
				if self.sentencefeatures[stftkey].endswith("#"): self.sentencefeatures[stftkey]=self.sentencefeatures[stftkey][:-1]
				treestring+="# "+self.sentencefeatures[stftkey]
			else:
				treestring+="# "+stftkey+" = "+self.sentencefeatures[stftkey]+"\n"	
		for i in sorted(self):
			node = self[i]                        
			govs=node.get("gov",{})
			govk = sorted(govs)
			if govk:
				gk,gv = str(govk[0]),govs.get(govk[0],"_")
			else:
				gk,gv = "_","_"
			treestring+="\t".join([
				str(i), 
				node.get("t","_"), 
				node.get("lemma",""), 
				node.get("tag","_"), 
				node.get("xpos","_"), 
				"|".join( [ a+"="+v for a,v in node.items() if a not in ["t","lemma","tag","tag2","xpos","egov","misc","id","index","gov","kids","govrel"]])  or "_", 
				gk,
				gv,
				"|".join( [ str(g)+":"+govs.get(g,"_") for g in govk[1:] ]) or "_", 
				node.get("misc","_")]) + "\n"
		return treestring

def update(d, u):
	for k, v in u.items():
		if isinstance(v, collections.Mapping):
			r = update(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d


def conll2tree(conllstring):
	""" 
	takes the conll string (or malt) representation of a single tree and creates a Tree (dictionary) for it
	"""
	tree=Tree()
	nr=1
	skipuntil=0 # only used to get the right "words" sequence, doesn't touch the actual tokens
	for line in conllstring.split('\n'):
		#print line
		if line.strip():
			if line.strip()[0]=="#": # comment of conllu
				if "=" in line:
					tree.sentencefeatures[line.split("=")[0].strip()[1:].strip()]="=".join(line.split("=")[1:]).strip()
				else:
					tree.sentencefeatures["_comments"]=tree.sentencefeatures.get("_comments","")+line.strip()[1:]+"\n#"
				continue
			
			cells = line.split('\t')
			nrCells = len(cells)
			
			if nrCells in [4,10,14]:
				
				if nrCells == 4: # malt!
					t, tag, govid, rel = cells
					if govid=="_": govid=-1
					else:govid = int(govid)
					newf={'id':nr,'t': t, 'tag': tag,'gov':{govid: rel}}
					tree[nr]=update(tree.get(nr,{}), newf)
					nr+=1

				elif nrCells == 10: # standard conll 10 or conllu
					nr, t, lemma , tag, xpos, features, govid, rel, edeps, misc = cells
					if "-" in nr: 
						try:	skipuntil=int(nr.split("-")[-1])
						except:	skipuntil=float(nr.split("-")[-1])
						tree.words+=[t]
						continue
					try:	nr = int(nr)
					except:	nr = float(nr) # handling the 3.1 format for "emtpy nodes"
					if govid.strip()=="_": govid=-1
					else:
						try:	govid = int(govid)
						except:	
							try:	govid = float(govid)
							except: 
								try:	assert(govid[0]=='$') # for transconll
								except: raise FormatError("not number or variable: "+govid)
					egov={}
					if ":" in edeps: # the enhanced graph is used
						egov=dict([(gf.split(":")[0],gf.split(":")[-1]) for gf in edeps.split("|")])					
					
					newf={'id':nr,'t': t,'lemma': lemma, 'tag': tag, 'xpos': xpos, 'gov':{govid: rel}, 'egov':egov, 'misc': misc}
					if "=" in features:
						mf=dict([(av.split("=")[0],av.split("=")[-1]) for av in features.split("|")])
						newf=update(mf,newf)
					
					tree[nr]=update(tree.get(nr,{}), newf)
					if nr>skipuntil: tree.words+=[t]
					
				elif nrCells == 14:
					#mate:
					#6, inscriptions, _, inscription, _, N, _, pl|masc, -1, 4, _, dep, _, _
					nr, t, lemma, lemma2, tag, xpos, morph, morph2, govid, govid2, rel, rel2, _, _ = cells
					nr = int(nr)
					if govid.strip()=="_": govid=-1
					else:govid = int(govid)
					if govid2.strip()=="_": govid2=-1
					else:govid2 = int(govid2)
					if lemma=="_" and lemma2!="_":lemma=lemma2
					if tag=="_" and xpos!="_":tag=xpos
					if morph=="_" and morph2!="_":morph=morph2
					if rel=="_" and rel2!="_":
						rel=rel2
						govid=govid2
					newf={'id':nr,'t': t,'lemma': lemma,'lemma2': lemma2, 'tag': tag, 'xpos': xpos, 'morph': morph, 'morph2': morph2, 'gov':{govid: rel}, 'egov':{govid2: rel2} }
					tree[nr]=update(tree.get(nr,{}), newf)
					
			elif debug:
				print("strange conll:",nrCells,"columns!",line)
	
	return tree


def conllFile2trees(path):
	"""
	file with path -> list of trees
	
	important function!	
	called from enterConll, treebankfiles, and uploadConll in treebankfiles.cgi
	
	"""
	trees=[]
	with open(path,"r") as f:
		conlltext=""
		for li in f:
			li=li.strip()
			if li: 	conlltext+=li+"\n"
			elif conlltext: # emptyline, sentence is finished
				tree=conll2tree(conlltext)
				trees+=[tree]
				del tree
				conlltext=""
		f.close()
		if conlltext.strip(): # last tree may not be followed by empty line
			tree=conll2tree(conlltext)
			trees+=[tree]
		return trees


def trees2conllFile(trees, outfile, columns="u"): # changed default from 10 to u!
	"""
	exports a list of treedics into outfile
	used after tree transformations...
	in conll14 format, the lemma position contains a duplicated t if lemma is not available
	"""
	with open(outfile,"w") as f:
		for tree in trees:
			if columns=="u": # conllu format
				treestring = tree.conllu()
			else:
				
				treestring = ""
				for stftkey in sorted(tree.sentencefeatures):
					if stftkey=="_comments":
						treestring+=tree.sentencefeatures[stftkey]
					else:
						treestring+=stftkey+" = "+tree.sentencefeatures[stftkey]				
				for i in sorted(tree):					
					node = tree[i] 
					gov = list(node.get("gov",{}).items())
					govid = -1
					func = "_"
					if gov:
						for govid,func in gov:
							if columns==10:
								treestring+="\t".join([str(i), node.get("t","_"), node.get("lemma",""), node.get("tag","_"), node.get("xpos","_"), "_", str(govid),func,"_","_"])+"\n"
							elif columns==14:
								lemma = node.get("lemma","_")
								if lemma == "_": lemma = node.get("t","_")
								treestring+="\t".join([str(i), node.get("t","_"), lemma, lemma or node.get("t","_"), node.get("tag","_"), node.get("tag","_"), node.get("morph","_"), node.get("morph","_"), str(govid),str(govid),func,func,"_","_"])+"\n"
					else:
						if columns==10:
							treestring+="\t".join([str(i), node.get("t","_"), node.get("lemma",""), node.get("tag","_"), node.get("xpos","_"), "_", str(govid),func,"_","_"])+"\n"
							
						elif columns==14:
							lemma = node.get("lemma","_")
							if lemma == "_": lemma = node.get("t","_")
							treestring+="\t".join([str(i), node.get("t","_"), lemma, lemma, node.get("tag","_"), node.get("tag","_"), node.get("morph","_"), node.get("morph","_"), str(govid),str(govid),func,func,"_","_"])+"\n"
			f.write(treestring+"\n")


def sentences2emptyConllFile(infile, outfile):
	"""
	transforms a list of sentences into conll format without trees
	"""
	inf=open(infile)
	outf=open(outfile,"w")
	counter=0
	for line in inf:
		line=line.strip()
		if line:
			for i,word in enumerate(line.split()):
				outf.write("\t".join([str(i+1),word,word,"_","_","_","-1","","_","_"])+"\n")
				## nr, t, lemma , tag, xpos, _, govid, rel, _, _ = cells
			outf.write("\n")
			counter+=1
	inf.close()
	outf.close()
	print(counter, "sentences")


def textFiles2emptyConllFiles(infolder, outfolder):
	import glob, os
	sentenceSplit=re.compile(r"(\s*\n+\s*|(?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])[\?\!？\!\.。！……]+\s+|\s+\|\s+|[？。！……]+)(?!\d)", re.M+re.U)
	resentence=re.compile(r"[\?\!？\!\.。！……]+", re.M+re.U)
	retokenize=re.compile("(\W)",re.U+re.I)
	redoublespace=re.compile("(\s+)",re.U+re.I)
	renumber=re.compile("(\d) \. (\d)",re.U+re.I)
	rewhite=re.compile("\w",re.U+re.I)
	try:os.mkdir(outfolder)
	except:print("folder exists")
	for infile in glob.glob(os.path.join(infolder, '*.*')):
		print(infile)
		outfile=open(outfolder+"/"+infile.split("/")[-1],"w")
		for line in open(infile):
			line=line.strip()
			for s in sentenceSplit.split(line):
				s=s.strip()
				if resentence.match(s):
					outfile.write(str(count)+"\t"+s+"\n")
					outfile.write("\n")
				else:
					count=1
					s = retokenize.sub(r" \1 ",s)
					s = redoublespace.sub(r" ",s)
					s = renumber.sub(r"\1.\2",s)
					for token in s.split():
						if token.strip()=='\ufeff':continue # TODO: find out why this anti BOM shit is needed...
						outfile.write(str(count)+"\t"+token+"\n")
						count +=1




if __name__ == "__main__":
	pass
	ts = conllFile2trees("th_pud-ud-test.conllu")
	print(len(ts))
	print(ts[0].conllu())
	print(ts[0].sentencefeatures)
	open("test.conllu","w").write(ts[0].conllu())
	

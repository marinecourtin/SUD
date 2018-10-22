#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2018 Kim Gerdes
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

"""
Conlleva. (it leads to, it puts up with)

Usage:
  conlleva.py tohtml <conllu_file>
  conlleva.py search <conllgrammar_file> <conllu_file> [--includeNonMatchingTrees]
  conlleva.py transform <transconllgrammar_file> <conllu_file> [--addStat]
  conlleva.py (-h | --help)
  conlleva.py (-v | --version)

Options:
  -h --help  Show this screen.
  -v --version  Show version.
  -i --includeNonMatchingTrees  include non-matching trees in the output file of search
  -a --addStat  add statistics in the output file of transform

Example Uses:
python3 conlleva.py tohtml "fr_sequoia-ud-test.conllu"
python3 conlleva.py search search.udauxaux.conllu fr_sequoia-ud-test.conllu --includeNonMatchingTrees
python3 conlleva.py transform UDtoSUD.txt fr_sequoia-ud-test.conllu --addStat

"""


import re, copy, os
from lib import conll, transconll, docopt

#import tqdm
#tqdm.monitor_interval = 0
try:
	import tqdm
	tqdm.monitor_interval = 0
except:
	pass

debug=False
#debug=True

htmltemplate=open("html/static/template.html").read()

htmlconll="""
<div class="panel-heading">
	<h2>{heading}</h2>
</div>
<div class="panel-body">
	<conll>
{conll}
	</conll>
</div> 
{stat}
"""

htmlstat="""
<div> 
<b>{title}:</b> total nb of relations: {nbrel}, nb of syntactic relations: {nbsynt}, total average dep dist: {distrel} average syntactic dep dist: {distsynt}, total right branching: {righttot}, syntactic right branching: {rightsynt}
</div> 
"""

def conll2html(inconll, sort=False):
	"""
	simple function: just creates an html file to view a conllu file
	
	"""
	basename = os.path.basename(inconll).split(".conllu")[0]
	print("doing",basename,"...")
	outhtml = "html/"+basename+".html"
	intrees = conll.conllFile2trees(inconll)#[:1]
	collectedConll=[]
	try: pbar = tqdm.tqdm(total=len(intrees))
	except: pass
	for i, intree in enumerate(intrees):
		try: pbar.update()
		except: pass
		collectedConll += [htmlconll.format(heading=str(i+1)+" "+intree.sentencefeatures.get('sent_id',''), conll=intree.conllu(), stat="")]
	if sort:
		collectedConll=sorted(collectedConll)
	with open(outhtml,"w") as outf:
		outf.write(htmltemplate.replace("{conll}","\n".join(collectedConll) ))
	print("written",outhtml)



def transConllView(grammar, inconll, outconllfolder="../conll/", outhtmlfolder="html/", addstat=False):
	"""
	inconll: an conll file as input
	grammar: transconll grammar
	function applies the grammar and writes out 
	- the transformed conll file
	- the diff html view file, both preceded by the name of the grammar
	"""
	conllbasename = os.path.basename(inconll).split(".conllu")[0]
	print("doing",conllbasename,"...")
	stat=""
	btnbrel, btnbsynt, btdistrel, btdistsynt, btrighttot, btrightsynt= 0,0,0,0,0,0
	atnbrel, atnbsynt, atdistrel, atdistsynt, atrighttot, atrightsynt= 0,0,0,0,0,0
	grammarbasename = os.path.basename(grammar).split(".")[0]
	outconll = outconllfolder+grammarbasename+"."+conllbasename+".conllu"
	outhtml = outhtmlfolder+grammarbasename+"."+conllbasename+".html"
	intrees = conll.conllFile2trees(inconll)#[:1]
	tr = transconll.TransGrammar(open(grammar).read())
	outconlls=[]
	collectedDoubleConll=""
	try: pbar = tqdm.tqdm(total=len(intrees))
	except: pass
	for i, intree in enumerate(intrees): # list(enumerate(intrees))[:3]
		try: pbar.update()
		except: pass
		outtree = copy.deepcopy(intree)
		tr.transform(outtree)
		tr.adddiff(intree, outtree)
		beforeconll = intree.conllu()
		afterconll = outtree.conllu()
		outconlls += [ afterconll ]
		if addstat: 
			nbrel, nbsynt, distrel, distsynt, righttot, rightsynt = simpleStat(intree)
			inhtmlstat=htmlstat.format(title="before", nbrel=nbrel, nbsynt=nbsynt, distrel=distrel, distsynt=distsynt, righttot=righttot, rightsynt=rightsynt)
			btdistrel=(btdistrel*btnbrel+distrel*nbrel)/(btnbrel+nbrel)
			btdistsynt=(btdistsynt*btnbsynt+distsynt*nbsynt)/(btnbsynt+nbsynt)
			btrighttot=(btrighttot*btnbrel+righttot*nbrel)/(btnbrel+nbrel)
			btrightsynt=(btrightsynt*btnbsynt+rightsynt*nbsynt)/(btnbsynt+nbsynt)
			btnbrel+=nbrel
			btnbsynt+=nbsynt
			binsofarhtmlstat=htmlstat.format(title="before so far", nbrel=btnbrel, nbsynt=btnbsynt, distrel=btdistrel, distsynt=btdistsynt, righttot=btrighttot, rightsynt=btrightsynt)
			
			nbrel, nbsynt, distrel, distsynt, righttot, rightsynt = simpleStat(outtree)
			outhtmlstat = htmlstat.format(title="after", nbrel=nbrel, nbsynt=nbsynt, distrel=distrel, distsynt=distsynt, righttot=righttot, rightsynt=rightsynt)
			atdistrel=(atdistrel*atnbrel+distrel*nbrel)/(atnbrel+nbrel)
			atdistsynt=(atdistsynt*atnbsynt+distsynt*nbsynt)/(atnbsynt+nbsynt)
			atrighttot=(atrighttot*atnbrel+righttot*nbrel)/(atnbrel+nbrel)
			atrightsynt=(atrightsynt*atnbsynt+rightsynt*nbsynt)/(atnbsynt+nbsynt)
			atnbrel+=nbrel
			atnbsynt+=nbsynt
			ainsofarhtmlstat=htmlstat.format(title="after so far", nbrel=atnbrel, nbsynt=atnbsynt, distrel=round(atdistrel,2), distsynt=round(atdistsynt,2), righttot=round(atrighttot,2), rightsynt=round(atrightsynt,2))
			stat = inhtmlstat + binsofarhtmlstat + outhtmlstat + ainsofarhtmlstat
		collectedDoubleConll += htmlconll.format(heading=str(i+1), conll=beforeconll +"\n\n"+afterconll, stat=stat)
		#break
	with open(outhtml,"w") as outf:
		outf.write(htmltemplate.replace("{conll}",collectedDoubleConll) )	
	with open(outconll,"w") as outf:
		outf.write("\n\n".join(outconlls))	
	print("written",outconll,"and",outhtml)
		
	

def simpleStat(tree):
	"""
	takes a conll tree
	returns 
	- total nb of relations
	- nb of syntactic relations
	- total average dep dist
	- average syntactic dep dist
	- total % right branching
	- syntactic % right branching
	"""
	syntactic = "nsubj csubj subj obj iobj ccomp xcomp aux cop case mark cc advmod advcl obl dislocated vocative expl nummod nmod amod discourse acl det".split()
	skipFuncs=['root']
	totdist, depdist, totright, depright = [], [], 0, 0
	for ni,node in tree.items():
		for gi in node["gov"]:
			func=node["gov"][gi]
			simfunc=func.split(":")[0]
		if simfunc not in skipFuncs:
			totdist += [abs(ni-gi)]
			if ni>gi: 
				totright += 1
			if simfunc in syntactic:
				depdist += [abs(ni-gi)]
				if ni>gi: 
					depright += 1
	return len(totdist), len(depdist), sum(totdist)/(len(totdist) or 1), sum(depdist)/(len(depdist) or 1), totright/(len(totdist) or 1)*100.0, depright/(len(depdist) or 1)*100.0


def searchConllView(grammar, inconll, outhtmlfolder="html/", includeNonMatchingTrees=False):
	"""
	inconll: an conll file as input
	grammar: search grammar, "or" relation between grammar trees
	function applies the grammar and writes out 
	- the diff html view file, preceded by the name of the grammar
	"""
	conllbasename = os.path.basename(inconll).split(".conllu")[0]
	print("doing",conllbasename,"...")
	stat=""
	
	grammarbasename = os.path.basename(grammar).split(".")[0]
	outhtml = outhtmlfolder+grammarbasename+"."+conllbasename+".html"
	intrees = conll.conllFile2trees(inconll)#[:1]
	sg = transconll.SearchGrammar(open(grammar).read())
	collectedConll=""
	try: pbar = tqdm.tqdm(total=len(intrees))
	except: pass
	for i, intree in enumerate(intrees): # list(enumerate(intrees))[:3]
		try: pbar.update()
		except: pass
		matchingRoots = sg.findall(intree)
		if matchingRoots or includeNonMatchingTrees:
			collectedConll += htmlconll.format(heading=str(i+1), conll=intree.conllu(), stat="")
	
	if collectedConll:
		with open(outhtml,"w") as outf:
			outf.write(htmltemplate.replace("{conll}",collectedConll) )	
		print("written",outhtml)
	else:
		print("no matches found")
		
	
		
if __name__ == "__main__":
	arguments = docopt.docopt(__doc__, version='Conlleva 1.0')
	#print("***",arguments)
	if 	arguments['tohtml']: 		conll2html(arguments['<conllu_file>'])
	elif 	arguments['search']: 		searchConllView(arguments['<conllgrammar_file>'], arguments['<conllu_file>'], includeNonMatchingTrees=arguments['--includeNonMatchingTrees'])
	elif 	arguments['transform']: 	transConllView(arguments['<transconllgrammar_file>'], arguments['<conllu_file>'], addstat=arguments['--addStat'])
	

"""
python3 conlleva.py tohtml "../ud-treebanks-v2.1/UD_French-Sequoia/fr_sequoia-ud-test.conllu"
python3 conlleva.py search search.udauxaux.conllu "../ud-treebanks-v2.1/UD_French-Sequoia/fr_sequoia-ud-test.conllu" -i

python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_French-Sequoia/fr_sequoia-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_French/fr-ud-dev.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_German/de-ud-dev.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_English/en-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Finnish/fi-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Korean/ko-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Cantonese/yue-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Chinese/zh-ud-test.conllu" -a
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Turkish/tr-ud-dev.conllu"
python3 conlleva.py transform UDtoSUD.txt "../ud-treebanks-v2.1/UD_Turkish/tr-ud-test.conllu"


"""

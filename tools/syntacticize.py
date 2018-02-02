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

import re, copy, os, time, multiprocessing, psutil
from lib import conll, transconll
try:
	import tqdm
	tqdm.monitor_interval = 0
except:
	pass


#debug=False
debug=True

grammarfile = "UDtoSUD.txt"
trgram = transconll.TransGrammar(open(grammarfile).read())

def syntacticize(inconll, filenameAddon=".SUD", skipIfPresent=True):
	"""
	single thread of conllu transformation by means of a transconll grammar
	"""
	basename = os.path.basename(inconll).split(".conllu")[0]
	print("doing",basename,"...")
	outconll = "conll/"+basename+filenameAddon+".conllu" 
	if skipIfPresent and os.path.isfile(outconll): 
		print("found already",basename)
		return # comment out to recompute
	intrees = conll.conllFile2trees(inconll)
	outconlls=[]
	#pbar = tqdm.tqdm(total=len(intrees))
	for i, intree in enumerate(intrees):
		#pbar.update()
		trgram.transform(intree)
		outconlls += [ intree.conllu() ]
	with open(outconll,"w") as outf:
		outf.write("\n\n".join(outconlls))
	print("done with",basename)
		
def syntacticizeAll(basefolder):
	"""
	main function: takes a basefolder, looks for all conllu files, creates a pool of threads to transform them
	"""
	ti = time.time()
	pool = multiprocessing.Pool(psutil.cpu_count()*2)
	codefiles = getAllConllFiles(basefolder)
	try: pbar = tqdm.tqdm(total=len(codefiles))
	except: pass
	results = []
	for res in pool.imap_unordered(syntacticize, codefiles):
		try: pbar.update()
		except: pass
		results.append(res)
	print("it took",time.time()-ti,"seconds for",len(results),"files")


def getAllConllFiles(basefolder):
	"""
	for a given basefolder, gives back a list of conll files 
	"""
	langConllFiles=[]
	for dirpath, dirnames, files in os.walk(basefolder):
		for f in files:
			if f.endswith(".conllu"):
				langConllFiles+=[os.path.join(dirpath,f)]
	return langConllFiles
		
if __name__ == "__main__":
	syntacticizeAll("../ud-treebanks-v2.1/")
	

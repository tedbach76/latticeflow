# tbach@bu.edu
# Makefile for the Simp documentation.
# Based on the Python 2.3.3 library documentation.

# You need mkhowto from the python distribution for creating this manual.
# Get a copy of a current python source archive and make a symbolic link
# from <whatever>/Python-x.x.x/Doc/tools/mkhowto into this directory.
# Furthermore you need tex, latex2html and a few other things to build
# the manual (see the python documentation about creating documentations
# for details).

# ./mkhowto
#MKHOWTO=/c/sources/Python-2.4.2/Doc/tools/mkhowto 

MKHOWTO=/usr/bin/python /c/sources/Python-2.4.2/Doc/tools/mkhowto -D
#MKHOWTO=/usr/bin/python ./tools/mkhowto


default: dvi 

dvi: simpmanual.dvi 

ps: simpmanual.ps

pdf: simpmanual.pdf

clean: 
	rm -f *.syn *.idx *.ind *.l2h *.log *.toc 
	rm -f *.pdf *.aux *.ps *.dvi
	rm -fr simpmanual

cleanall: clean
	rm -rf xfig/*.eps xfig/*.bak
	rm -rf ppm/*.ps
	rm -rf simpppm/*.ps
#	rm -rf simp/*.eps
	rm -rf benchmark/*.eps
	rm -rf simpppm/*.ppm
#	rm -f html-$(RELEASE).tar
#	rm -rf html/index.html html/modindex.html html/acks.html
#	rm -rf html/simpmanual/*
#	rm -f 
#	rm -fr paper-$(PAPER)/xfig
#	rm -fr paper-$(PAPER)/ps
#	rm -fr paper-$(PAPER)/ppm

src=$(wildcard *.tex) $(wildcard xfig/*.fig) $(wildcard ppm/*.ppm) $(wildcard simpppm/*.ps) xfig_to_eps ppm_to_ps simpfigs 
PAPER=letter

simpmanual.dvi: $(src) benchmark
	${MKHOWTO} --$(PAPER) --dvi simpmanual.tex

simpmanual.ps: simpmanual.dvi
	dvips -N0 -t $(PAPER) simpmanual -o simpmanual.ps

simpmanual.pdf: simpmanual.ps
	ps2pdf simpmanual.ps

html: simpmanual/simpmanual.html

# MKHOWTO HTML NOTES
# \var{} inside of a caption causes: 
#    defining handler for \leftmargin using \leftmargini
#    .............Undefined subroutine &main::do_cmd_leftmargini called at (eval 670) line 1.
#    *** Session transcript and error messages are in /home/tbach/cvs/simp/Doc/Manual/simpmanual/simpmanual.how.
#    *** Exited with status 25.

simpmanual/simpmanual.html: # $(src) 
	./mkhowto --html \
	          --favicon "/simpfav.gif" \
	          --up-link "/" --up-title "SIMP Homepage" \
		   simpmanual.tex 

#pyxversion.tex: ../pyx/version.py
#	python -c "import sys;sys.path[:0]=[\"..\"];import pyx.version;print pyx.version.version+'%'" > pyxversion.tex


#eps: $(patsubst %.py, %.eps, $(wildcard *.py))
#png: $(patsubst %.py, %.png, $(wildcard *.py))
#
#%.eps: %.py
#	export PYTHONPATH=$(CURDIR)/.. ; python $^
#
#%.png: %.eps
#	gs -dEPSCrop -dNOPAUSE -dQUIET -dBATCH -sDEVICE=png16m -sOutputFile=$@ -r600 $^


############################ EPS FIGURES ################################
# convert fig files in the xfig directory to ps files
XFIG_FILES=$(wildcard xfig/*.fig)
XFIG_EPS_FILES= $(XFIG_FILES:.fig=.eps)

xfig_to_eps: $(XFIG_EPS_FILES)

xfig/%.eps:	xfig/%.fig
#	fig2dev -L eps $<  > $@
	fig2dev -L eps -g "#ffffff" $<  > $@

############################ ppm conversion ################################
# compile eps files from png files
PPM_FILES=$(wildcard ppm/*.ppm)
PPM_PS_FILES=$(PPM_FILES:.ppm=.ps)
ppm_to_ps: $(PPM_PS_FILES)

ppm/%.ps:	ppm/%.ppm
	pnmtops -noturn -nosetpage -nocenter $< > $@ 

############################ SIMP GENERATED FIGURES #########################
simpfigs: simpppm # First make the .ppm files 
	make simpps # then convert them to .ps files. must be done recursively 
# so that the makefile pattern substitution will pick up the new .ppm files. 


simpppm: $(patsubst %.py, %.ppm, $(wildcard simpppm/*.py))

simpps: $(patsubst %.ppm, %.ps, $(wildcard simpppm/*.ppm))


#export PYTHONPATH=$(PYTHONPATH):$(CURDIR)/../../lib

simpppm/%.ppm: simpppm/%.py
#	cd simp;
#	export PYTHONPATH=$(PYTHONPATH):./../../../lib
	python $^
	mv -f *.ppm simpppm

simpppm/%.ps:	simpppm/%.ppm
	pnmtops -noturn -nosetpage -nocenter $< > $@ 


############################ BENCHMARKING FIGURES #########################
benchmark:  benchmark/parityneighbors.eps 

BENCHDEPS = benchmark/benchmarkplots.py  benchmark/parallelplots.py
benchmark/parityneighbors.eps:  $(BENCHDEPS)
	echo "commented python benchmark/benchmarkplots.py in Makefile "
#	python benchmark/benchmarkplots.py
#	python benchmark/parallelplots.py



#Diffusion1DGrid.py Diffusion1DGridBlock.py Diffusion1DGridNoShift.py \
#         Diffusion1DSubLat.py




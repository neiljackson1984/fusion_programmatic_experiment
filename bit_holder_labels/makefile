buildDirectory=build
# buildDirectory:=$(shell mktemp --directory --dry-run)

#the next three variables are just for the tiled output.
inputFile=labels.tex
texOutputFile=${buildDirectory}/labels.pdf
tiledOutputFile=$(basename ${texOutputFile})-tiled.pdf


texFileExtensions=tex latex plaintex
allTexFiles=$(foreach texFileExtension, ${texFileExtensions}, $(wildcard ./*.${texFileExtension}))
allOutputPdfFiles=$(foreach texFile,${allTexFiles}, ${buildDirectory}/$(basename $(notdir ${texFile})).pdf)

# latexRecipe=miktex-xetex --quiet --undump=xelatex --interaction=nonstopmode --aux-directory="$(shell cygpath --windows $(abspath ${buildDirectory}))" --output-directory="$(shell cygpath --windows $(abspath $(dir ${@})))" --job-name="$(basename $(notdir ${@}))" "$(shell cygpath --windows $(abspath ${<}))"
# plainTexRecipe=xetex.exe -synctex=1 -interaction=nonstopmode --aux-directory="$(shell cygpath --windows $(abspath ${buildDirectory}))" --output-directory="$(shell cygpath --windows $(abspath $(dir ${@})))" "$(shell cygpath --windows $(abspath ${<}))"

latexRecipe=-miktex-xetex --quiet --shell-escape --undump=xelatex --interaction=nonstopmode --aux-directory="$(shell cygpath --windows $(abspath ${buildDirectory}))" --output-directory="$(shell cygpath --windows $(abspath $(dir ${@})))" --job-name="$(basename $(notdir ${@}))" "$(shell cygpath --windows $(abspath ${<}))"
plainTexRecipe=-xetex.exe -synctex=1 -interaction=nonstopmode --aux-directory="$(shell cygpath --windows $(abspath ${buildDirectory}))" --output-directory="$(shell cygpath --windows $(abspath $(dir ${@})))" "$(shell cygpath --windows $(abspath ${<}))"


default: ${allOutputPdfFiles} ${tiledOutputFile}
#default: ${allOutputPdfFiles}

#the following two line is just for experimenting with the vboxes and hboxes.
${buildDirectory}/labels.pdf ${buildDirectory}/textest.pdf: includeme.tex

#the following rule will prevent includeme.tex from being compiled.
${buildDirectory}/includeme.pdf:
	@#do nothing

${tiledOutputFile}: ${texOutputFile} tile.php makefile
	php tile.php --inputPdfFile="$(shell cygpath --windows $(abspath ${texOutputFile}))" --outputPdfFile="$(shell cygpath --windows $(abspath ${tiledOutputFile}))" --outputPageWidth=8.5inch --outputPageHeight=11inch --outputPageLeftMargin=1inch --outputPageRightMargin=1inch --outputPageTopMargin=1inch --outputPageBottomMargin=1inch --dividerLineThickness=0.0004in

#the following line simply declares that any target m,atching the rule ${buildDirectory}/% depends on ${buildDirectory}
${buildDirectory}/%: ${buildDirectory} 

${buildDirectory}/%.pdf:%.tex 
	${latexRecipe}

${buildDirectory}/%.pdf:%.latex
	${latexRecipe}

${buildDirectory}/%.pdf:%.plaintex
	${plainTexRecipe}

${buildDirectory}:
	echo making the build directory: ${buildDirectory}
	mkdir --parents ${buildDirectory}
	
# .SILENT:
	


	
#===== CRAP: ============================================
# @echo allTexFiles: ${allTexFiles}
# @echo allOutputPdfFiles: ${allOutputPdfFiles}

#this is what TexStudio view by default.
#viewableOutputFile=$(basename ${inputFile}).pdf
# @# echo target is ${@}
# @# echo first prerequisite is ${<} 
#  automatic variables reminder:
#   $@ -- this is the target (i.e. the thing that we are making)
#   $< -- this is the the first prerequisite.


# ${texOutputFile}: ${inputFile} ${buildDirectory}
# @# miktex-xetex --quiet --undump=xelatex --interaction=nonstopmode --output-directory=\"$tempDirectory\" --aux-directory=\"$tempDirectory\"" ." ". "\"$texFile\" 
# miktex-xetex --quiet --undump=xelatex --interaction=nonstopmode --aux-directory="$(shell cygpath --windows $(abspath ${buildDirectory}))" --output-directory="$(shell cygpath --windows $(abspath $(dir ${texOutputFile})))" --job-name="$(basename $(notdir ${texOutputFile}))" "$(shell cygpath --windows $(abspath ${inputFile}))"
		
	
#untiledPsFile=$(basename ${texOutputFile}).ps
#tiledPsFile=$(basename ${texOutputFile})-tiled.ps
# @# pdftops -paper match "$(shell cygpath --windows $(abspath ${texOutputFile}))" "$(shell cygpath --windows $(abspath ${untiledPsFile}))"
# @# # pstops -q -d0.0 -w9mm -h12mm "$(shell cygpath --windows $(abspath ${untiledPsFile}))" "$(shell cygpath --windows $(abspath ${tiledPsFile}))"
# @# psnup -w8.5in -h11in -d0.001in -W0.9cm -H1.2cm -m0 -b0 -s1 -20 -q "$(shell cygpath --windows $(abspath ${untiledPsFile}))" "$(shell cygpath --windows $(abspath ${tiledPsFile}))"
# @# gswin64 -q -sPAPERSIZE=letter -dSAFER -dNOPAUSE -dBATCH -sOutputFile="$(shell cygpath --windows $(abspath ${tiledOutputFile}))"  -sDEVICE=pdfwrite  -c .setpdfwrite -f "$(shell cygpath --windows $(abspath ${tiledPsFile}))"
	
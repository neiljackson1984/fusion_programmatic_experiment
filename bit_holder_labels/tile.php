<?php

$ghostscriptExecutable="gswin64c"; //Whereas "gswin64.exe" is ghostscript with GUI (so it pops up a window), "gswin64c.exe" is designed to be run from the command line, so does not create a window.
$ghostviewExecutable="gsview64";

$options = 
	getopt("",
		[
			"inputPdfFile:",
			"outputPdfFile:",
			"outputPageWidth:",
			"outputPageHeight:",
			"outputPageLeftMargin:",
			"outputPageRightMargin:",
			"outputPageTopMargin:",
			"outputPageBottomMargin:",
			"dividerLineThickness:"
		]
	);

$inputPdfFile = realpath($options['inputPdfFile']);

$outputPdfFile = get_absolute_path($options['outputPdfFile']);

$units = [];
$units['point']=1;
$units['inch']=72*$units['point'];

// echo "\$options: " . var_export($options, true) . "\n";

$outputPageWidth         =getPhysicalValue($options['outputPageWidth']);
$outputPageHeight        =getPhysicalValue($options['outputPageHeight']);
$outputPageLeftMargin    =getPhysicalValue($options['outputPageLeftMargin']);
$outputPageRightMargin   =getPhysicalValue($options['outputPageRightMargin']);
$outputPageTopMargin     =getPhysicalValue($options['outputPageTopMargin']);
$outputPageBottomMargin  =getPhysicalValue($options['outputPageBottomMargin']);
$dividerLineThickness    =getPhysicalValue($options['dividerLineThickness']);

// echo "\$outputPageWidth        : " . $outputPageWidth         . "\n";
// echo "\$outputPageHeight       : " . $outputPageHeight        . "\n";
// echo "\$outputPageLeftMargin   : " . $outputPageLeftMargin    . "\n";
// echo "\$outputPageRightMargin  : " . $outputPageRightMargin   . "\n";
// echo "\$outputPageTopMargin    : " . $outputPageTopMargin     . "\n";
// echo "\$outputPageBottomMargin : " . $outputPageBottomMargin  . "\n";


//$outputPageMargin=1*$units['inch'];
$maximumAllowableNumberOfTilesPerPage = 152; //this seems to be a limitation built into pstops.  If we pass pstops a pagespec that contains more than 152 tiles, pstops causes a segmentation fault (but 152 or less seems to work fine).
 
//define all the temporary file names we might need:
$tempDirectory=tempnam(sys_get_temp_dir(), '');
unlink($tempDirectory); //tempnam creates a file, not a directory, so we need to delete the file and create a folder of the same name.
if(!file_exists($tempDirectory)) {mkdir($tempDirectory);} else { /*delete everything from temp directory here?*/} ;
$tempDirectory=realpath($tempDirectory);
$uniqueRootName = uniqid();
$mergedPdfFile = $inputPdfFile;
$mergedPsFile = $tempDirectory . DIRECTORY_SEPARATOR  . $uniqueRootName . ".ps";
$tiledPsFile = $tempDirectory . DIRECTORY_SEPARATOR  . $uniqueRootName . "-tiled.ps";
$tempShellScriptFile = $tempDirectory . DIRECTORY_SEPARATOR  . $uniqueRootName . "-shellscript.sh";
$temporaryTiledPdfFile = $tempDirectory . DIRECTORY_SEPARATOR  . $uniqueRootName . "-tiled.pdf";

	
//we assume that all pages in the input pdf file are the same size, so we will only bother to look at the page size of the first page.

//use pdfinfo (part of xpdf toolkit) to get the page size of the input pdf file.
//echo "inputPdfFile: " . $inputPdfFile . "\n";
//echo "temporaryTiledPdfFile: " . $temporaryTiledPdfFile . "\n";
$command = "pdfinfo -box -f 1 -l -1 " . "\"" . $inputPdfFile . "\"";
//echo "command: " . $command . "\n";
$pdfinfoReport = shell_exec($command);

// look for a line like "Page    1 size: 25.51 x 34.02 pts (rotated 0 degrees)"
$regExForPageSizeLine = "/^page\\s*(?P<pageNumber>\\d+)\\s*size:\\s*(?P<pageWidth>[\\d\.]+)\\s*x\\s*(?P<pageHeight>[\\d\.]+)\\s*(?P<lengthUnits>\\w+)\\s*(\\(rotated\\s*(?P<rotationAngle>[\\d\.]+)\\s*(?P<angularUnits>\\w+)\\s*\\)|).*$/mi";
preg_match_all($regExForPageSizeLine, $pdfinfoReport, $matches, PREG_SET_ORDER);
//echo $pdfinfoReport;
//echo "matches: " .  "\n" . var_export($matches, true) . "\n";
//echo "\$regExForPageSizeLine: " . $regExForPageSizeLine . "\n";
$lengthUnits=$matches[0]['lengthUnits'];
$tileWidth=getPhysicalValue($matches[0]['pageWidth'] . $matches[0]['lengthUnits']);
	
$tileHeight=getPhysicalValue($matches[0]['pageHeight'] . $matches[0]['lengthUnits']);

//  $angularUnits=$matches[0]['angularUnits'];
//  $rotationAngle=$matches[0]['rotationAngle'];
//  proper handling of rotation other than zero is not yet implemented.


echo "Converting the pdf file ino postscript...\n";
exec("pdftops -paper match \"$mergedPdfFile\" \"$mergedPsFile\"");

$tileExtent = 
	[
		$tileWidth,
		$tileHeight
	];

$extentOfMaximumAllowableTilingArea = 
	[
		$outputPageWidth-$outputPageLeftMargin-$outputPageRightMargin,
		$outputPageHeight-$outputPageTopMargin-$outputPageBottomMargin
	];
	
$cornerOfMaximumAllowableTilingArea = 
	[
		$outputPageLeftMargin,
		$outputPageBottomMargin
	];

$tileCount = 
	[
		floor($extentOfMaximumAllowableTilingArea[0]/$tileExtent[0]),
		floor($extentOfMaximumAllowableTilingArea[1]/$tileExtent[1])
	];

$extentOfTilingArea = 
	[
		$tileCount[0] * $tileExtent[0],
		$tileCount[1] * $tileExtent[1]
	];
	
$cornerOfTilingArea = 
	[
		$cornerOfMaximumAllowableTilingArea[0] + ($extentOfMaximumAllowableTilingArea[0] - $extentOfTilingArea[0])/2,
		$cornerOfMaximumAllowableTilingArea[1] + ($extentOfMaximumAllowableTilingArea[1] - $extentOfTilingArea[1])/2
	];

	
$insertionPoints = [];
for($yIndex = $tileCount[1] - 1; $yIndex >=0 ; $yIndex--)	
{
	for($xIndex = 0; $xIndex < $tileCount[0]; $xIndex++)	
	{
		array_push($insertionPoints,
			[
				$cornerOfTilingArea[0] + $tileExtent[0] * $xIndex,
				$cornerOfTilingArea[1] + $tileExtent[1] * $yIndex				
			]
		);
	}
}


$insertionPoints = array_slice($insertionPoints, 0, $maximumAllowableNumberOfTilesPerPage );

$pagespecForPstops = "";
$pagespecForPstops .= count($insertionPoints) . ":";
$isFirst=true;
for($i=0; $i < count($insertionPoints); $i++)
{
	$pagespecForPstops .= 
		($isFirst?"":"+") .
		$i .
		"(" . 
			//($insertionPoints[$i][0]/$units['inch'])."in" .",". ($insertionPoints[$i][1]/$units['inch'])."in".
			($insertionPoints[$i][0]/$units['point'])     .",". ($insertionPoints[$i][1]/$units['point']) . 
		")";
	$isFirst=false;
}

//echo "\$pagespecForPstops : " . print_r($pagespecForPstops ,true) . "\n";
$command = 
	"pstops"                                               ." ".
	"-q"                                                   ." ". //suppresses the page numbers that pstops would otherwise print on the tiled output
	"-d". ($dividerLineThickness/$units['point']) . "pt"   ." ".
	"-w". ($tileExtent[0]/$units['point']) . "pt"          ." ". 
	"-h". ($tileExtent[1]/$units['point']) . "pt"          ." ".
	"\"". $pagespecForPstops . "\""                        ." ". 
	"\"". addslashes($mergedPsFile) . "\""                 ." ".
	"\"". addslashes($tiledPsFile)  . "\""                 ." ".
	"";

//$pageSpecForPstops tends to be a very long string, which tends to cause the command to exceed the maximum allowed command length for the Windows shell.
//Therefore, I use sh instead	
	
$shellScript = 
	"#!/bin/sh" . "\n" .
	$command . "\n" .
	"";
file_put_contents($tempShellScriptFile, $shellScript);
$command = "sh " . "\"" . $tempShellScriptFile . "\"" ;	
//echo "command: " . $command . "\n";
//echo "\n";
exec($command);
 
echo "Converting tiled postscript file into final pdf output file...\n";
$command =
	$ghostscriptExecutable                              ." ".
	"-q"                                                ." ".
	//"-sPAPERSIZE=letter"                              ." ".
	"-dDEVICEWIDTHPOINTS="  .($outputPageWidth/$units['point'])  ." ".
	"-dDEVICEHEIGHTPOINTS=" .($outputPageHeight/$units['point']) ." ".
	"-dSAFER"                                           ." ".
	"-dNOPAUSE"                                         ." ".
	"-dBATCH"                                           ." ".
	"-sOutputFile=" . "\"".$temporaryTiledPdfFile."\""          ." ".
	"-sDEVICE=pdfwrite"                                 ." ".
	"-c .setpdfwrite"                                   ." ".
	"-f" . "\"".$tiledPsFile."\""                       ." ".
	""; 
//echo "command: " . $command . "\n";	
exec($command);


//copy $temporaryTiledPdfFile to $outputPdfFile
copy($temporaryTiledPdfFile, $outputPdfFile);
echo "Cleaning up temp files..." . "\n";
rrmdir($tempDirectory);









//from http://www.php.net/%20realpath : 
function get_absolute_path($path) {
        $path = str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $path);
        $parts = array_filter(explode(DIRECTORY_SEPARATOR, $path), 'strlen');
        $absolutes = array();
        foreach ($parts as $part) {
            if ('.' == $part) continue;
            if ('..' == $part) {
                array_pop($absolutes);
            } else {
                $absolutes[] = $part;
            }
        }
        return implode(DIRECTORY_SEPARATOR, $absolutes);
    }


 
/**
 * Recursively removes a folder along with all its files and directories
	*
 * @param String $path
 * 
 * COPIED FROM http://ben.lobaugh.net/blog/910/php-recursively-remove-a-directory-and-all-files-and-folder-contained-within
 */
function rrmdir($path) {
	// Open the source directory to read in files
	$i = new DirectoryIterator($path);
	foreach($i as $f) {
		if($f->isFile()) {
			unlink($f->getRealPath());
		} else if(!$f->isDot() && $f->isDir()) {
			rrmdir($f->getRealPath());
		}
	}
	rmdir($path);
}

//takes a string like "3.5 inch" and returns the floating point value, using $units to convert to the standard units.
function getPhysicalValue($string)
{
	global $units;
	
	preg_match_all(
		"/.*?(?P<value>[\\d\.]+)\\s*(?P<nameOfUnit>\\w+).*/i", 
		$string, 
		$matches, 
		PREG_SET_ORDER
	);
	//echo "\$matches: " . var_export($matches, true) . "\n";
	if(
		count($matches) >= 1 && array_key_exists('value', $matches[0]) && array_key_exists('nameOfUnit', $matches[0])
	)
	{
		return 
			floatval($matches[0]['value']) * 
			[
				"pts" => $units['point'],
				"pt" => $units['point'],
				"point" => $units['point'],
				"points" => $units['point'],
				"ins" => $units['inch'],
				"in" => $units['inch'],
				"inch" => $units['inch'],
				"inches" => $units['inch'],
			][strtolower($matches[0]['nameOfUnit'])];
	} else
	{
		trigger_error("getPhysicalValue() was passed an invalid string: " . $string, E_USER_WARNING);
		return null;
	}
}



?>
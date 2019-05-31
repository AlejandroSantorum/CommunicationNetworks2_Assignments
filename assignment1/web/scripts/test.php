<?php
$f = fopen( 'php://stdin', 'r' );
stream_set_blocking($f, false);

$html_part1 = '<doctype html><html><head><meta charset=\"UTF-8\"></head><body>';
$html_part2 = '</body></html>';
$FILENAME = '/post_response.html'; # Easier to open it on root_server file

$file = fopen( __DIR__ . "/../post_response.html", "wb");
fwrite($file, $html_part1);

$aux_flag = 0;
fwrite($file, '<b><p>Parametros recibidos por STDIN:</p></b><p style="color:#FE2EF7";>');
while( $line = fgets( $f ) ) {
    $aux_flag = 1;
  fwrite($file, $line);
}
if($aux_flag == 1){
    fwrite($file, ', a las ');
    fwrite($file, date('l jS \of F Y h:i:s A'));
}
fwrite($file, '</p>');

fwrite($file, '<b><p>Parametros recibidos por ARGV:</p></b><p style="color:#04B431";>');
for($i=1; $i<$argc; $i++){
    fwrite($file, $argv[$i]);
    if($i == $argc-1){
        fwrite($file, ', a las ');
        fwrite($file, date('l jS \of F Y h:i:s A'));
    }
}
fwrite($file, '</p>');

fwrite($file, $html_part2);

echo $FILENAME;
fclose($file);
fclose( $f );
?>

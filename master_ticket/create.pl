use strict;
use JSON;
use SOAP::Lite;
my $USE_PROXY_SERVER = 1;
my $soap = new SOAP::Lite;

use lib qw(..);
use JSON qw( );

my $filename = 'credentials.json';

my $json_text = do {
   open(my $json_fh, "<:encoding(UTF-8)", $filename)
      or die("Can't open \$filename\": $!\n");
   local $/;
   <$json_fh>
};

my $json = JSON->new;
my $credentials = $json->decode($json_text);

if ($#ARGV + 1 != 2) {
    print "\nUsage: name.pl first_name last_name\n";
    exit;
}



$soap->uri('https://footprints.sdsc.edu/MRWebServices');
$soap->proxy( 'https://footprints.sdsc.edu/MRcgi/MRWebServices.pl' );

my $projfields = decode_json $ARGV[1];

#my $soapenv = $soap->MRWebServices__editIssue(
my $soapenv = $soap->MRWebServices__createIssue(
    $credentials->{footprints_username},
    $credentials->{footprints_password},
    '',
    $projfields
);

if( $soapenv->fault ){
    print ${$soapenv->fault}{faultstring} . "\n";
    exit;
}
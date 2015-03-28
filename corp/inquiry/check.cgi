#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ POST-MAIL : check.cgi - 2011/10/29
#│ copyright (c) KentWeb
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);

# 外部ファイル取り込み
require './init.cgi';
my %cf = &init;

print <<EOM;
Content-type: text/html

<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8">
<title>Check Mode</title>
</head>
<body>
<b>Check Mode: [ $cf{version} ]</b>
<ul>
<li>Perlバージョン : $]
EOM

# ログファイル
if (-f $cf{logfile}) {
	print "<li>ログファイルパス : OK\n";

	if (-r $cf{logfile} && -w $cf{logfile}) {
		print "<li>ログファイルパーミッション : OK\n";
	} else {
		print "<li>ログファイルパーミッション : NG\n";
	}
} else {
	print "<li>ログファイルパス : NG\n";
}

# メールソフトチェック
print "<li>sendmailパス：";
if (-e $cf{sendmail}) {
	print "OK\n";
} else {
	print "NG\n";
}

# テンプレート
my @tmpl = qw|conf.html err1.html err2.html thx.html mail.txt reply.txt|;
foreach (@tmpl) {
	print "<li>テンプレート ( $_ ) : ";

	if (-f "$cf{tmpldir}/$_") {
		print "パスOK\n";
	} else {
		print "パスNG\n";
	}
}

print <<EOM;
</ul>
</body>
</html>
EOM
exit;


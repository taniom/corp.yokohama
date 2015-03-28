#!/usr/bin/perl

#┌─────────────────────────────────
#│ POST-MAIL : postmail.cgi - 2011/12/18
#│ copyright (c) KentWeb
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール実行
use strict;
use CGI::Carp qw(fatalsToBrowser);
use lib './lib';
use CGI::Minimal;
use Jcode;

# Jcode宣言
my $j = new Jcode;

# 設定ファイル認識
require "./init.cgi";
my %cf = &init;

# データ受理
CGI::Minimal::max_read_size($cf{maxdata});
my $cgi = CGI::Minimal->new;
&error('容量オーバー') if ($cgi->truncated);
my ($key,$need,$in) = &parse_form;

# 禁止ワードチェック
if ($cf{no_wd}) {
	my $flg;
	foreach (@$key) {
		foreach my $wd ( split(/,/, $cf{no_wd}) ) {
			if (index($$in{$_},$wd) >= 0) {
				$flg++;
				last;
			}
		}
		if ($flg) { &error("禁止ワードが含まれています"); }
	}
}

# ホスト取得＆チェック
my ($host,$addr) = &get_host;

# 必須入力チェック
my ($check,@err,@need);
if ($$in{need} || @$need > 0) {

	# needフィールドの値を必須配列に加える
	my @tmp = split(/\s+/, $$in{need});
	push(@need,@tmp);

	# 必須配列の重複要素を排除する
	my (@uniq,%seen);
	foreach (@need) {
		push(@uniq,$_) unless $seen{$_}++;
	}

	# 必須項目の入力値をチェックする
	foreach (@uniq) {

		# フィールドの値が投げられてこないもの（ラジオボタン等）
		if (!defined($$in{$_})) {
			$check++;
			push(@$key,$_);
			push(@err,$_);

		# 入力なしの場合
		} elsif ($$in{$_} eq "") {
			$check++;
			push(@err,$_);
		}
	}
}

# 入力内容マッチ
my ($match1,$match2);
if ($$in{match}) {
	($match1,$match2) = split(/\s+/, $$in{match}, 2);

	if ($$in{$match1} ne $$in{$match2}) {
		&error("$match1と$match2の再入力内容が異なります");
	}
}
# 2015.3.21 コメントアウト
# 2015.3.22 コメントアウト解除

#入力チェック確認画面
if ($check) {
	&err_check($match2);
}
# 2015.3.21 コメントアウト
# 2015.3.22 コメントアウト解除

# E-mail形式チェック
if ($$in{email} =~ /\,/) {
	&error("メールアドレスにコンマ ( , ) が含まれています");
}
if ($$in{email} ne '' && $$in{email} !~ /^[\w\.\-]+\@[\w\.\-]+\.[a-zA-Z]{2,}$/) {
	&error("メールアドレスの形式が不正です");
}

# --- プレビュー
if ($$in{mode} ne "send" && $cf{preview}) {

	# 連続送信チェック
	&check_post('view');

	# 確認画面
	&preview;

# --- 送信実行
} else {

	# 連続送信チェック
	&check_post('send');

	# sendmail送信
	&send_mail;
}

#-----------------------------------------------------------
#  プレビュー
#-----------------------------------------------------------
sub preview {
	# 送信内容チェック
	&error("データを取得できません") if (@$key == 0);

	# 時間取得
	my $time = time;

	# テンプレート読込
	open(IN,"$cf{tmpldir}/conf.html") or &error("open err: conf.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# テンプレート分割
	my ($head,$loop,$foot);
	if ($tmpl =~ /(.+)<!-- cell_begin -->(.+)<!-- cell_end -->(.+)/s) {
		($head,$loop,$foot) = ($1,$2,$3);
	} else {
		&error("テンプレートが不正です");
	}

	# 引数
	my $hidden = qq|<input type="hidden" name="mode" value="send" />\n|;

	# 項目
	my ($bef,$item);
	foreach my $key (@$key) {
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($$in{match} && $key eq $match2);
# 2015.3.21 コメントアウト
# 2015.3.22 コメントアウト解除
		if ($key eq 'subject') {
			$hidden .= qq|<input type="hidden" name="$key" value="$$in{subject}" />\n|;
			next;
		}

		# 引数
		$hidden .= qq|<input type="hidden" name="$key" value="$$in{$key}" />\n|;

		# 改行変換
		$$in{$key} =~ s|\t|<br />|g;

		my $tmp = $loop;
		if (defined($cf{replace}->{$key})) {
			$tmp =~ s/!key!/$cf{replace}->{$key}/;
		} else {
			$tmp =~ s/!key!/$key/;
		}
		$tmp =~ s/!val!/$$in{$key}/;
		$item .= $tmp;

		$bef = $key;
	}

	# 文字置換
	for ( $head, $foot ) {
		s/!mail_cgi!/$cf{mail_cgi}/g;
		s/<!-- hidden -->/$hidden/g;
	}

	# 画面展開
	print "Content-type: text/html\n\n";
	print $head, $item;

	# フッタ表示
	&footer($foot);
}

#-----------------------------------------------------------
#  送信実行
#-----------------------------------------------------------
sub send_mail {
	# 送信内容チェック
	&error("データを取得できません") if (@$key == 0);

	# 時間取得
	my ($date1,$date2) = &get_time;

	# ブラウザ情報
	my $agent = $ENV{HTTP_USER_AGENT};
	$agent =~ s/[<>&"'()+;]//g;

	# 本文テンプレ読み込み
	my $tbody;
	open(IN,"$cf{tmpldir}/mail.txt") or &error("open err: mail.txt");
	my $tbody = join('', <IN>);
	close(IN);

	# 改行
	$tbody =~ s/\r\n/\n/g;
	$tbody =~ s/\r/\n/g;

	# テンプレ変数変換
	$tbody =~ s/!date!/$date1/g;
	$tbody =~ s/!agent!/$agent/g;
	$tbody =~ s/!host!/$host/g;
#	$tbody = $j->set(\$tbody,'utf8')->jis;
	$tbody = $j->set(\$tbody,'utf8')->utf8;

	# 自動返信ありのとき
	my $resbody;
	if ($cf{auto_res}) {

		# テンプレ
		open(IN,"$cf{tmpldir}/reply.txt") or &error("open err: reply.txt");
		$resbody = join('', <IN>);
		close(IN);

		# 改行
		$resbody =~ s/\r\n/\n/g;
		$resbody =~ s/\r/\n/g;

		# 変数変換
		$resbody =~ s/!date!/$date1/g;
#		$resbody = $j->set(\$resbody,'utf8')->jis;
		$resbody = $j->set(\$resbody,'utf8')->utf8;
	}

	# 2015.2.15 問合せ人の会社
	my $inquirerCom;

	# 2015.2.15 問合せ人の名前
	my $inquirerNm;

	# 本文キーを展開
	my ($bef,$mbody,$log);
	foreach (@$key) {

		# 本文に含めない部分を排除
		next if ($_ eq "mode");
		next if ($_ eq "need");
		next if ($_ eq "match");
		next if ($_ eq "subject");
		next if ($$in{match} && $_ eq $match2);
# 2015.3.21 コメントアウト
# 2015.3.22 コメントアウト解除
		next if ($bef eq $_);

		# name値の名前置換
		my $key_name = defined($cf{replace}->{$_}) ? $cf{replace}->{$_} : $_;

		# エスケープ
		$$in{$_} =~ s/\.\n/\. \n/g;

		# 添付ファイル風の文字列拒否
		$$in{$_} =~ s/Content-Disposition:\s*attachment;.*//ig;
		$$in{$_} =~ s/Content-Transfer-Encoding:.*//ig;
		$$in{$_} =~ s/Content-Type:\s*multipart\/mixed;\s*boundary=.*//ig;

		# 改行復元
		$$in{$_} =~ s/\t/\n/g;

		# HTMLタグ復元
		$$in{$_} =~ s/&lt;/</g;
		$$in{$_} =~ s/&gt;/>/g;
		$$in{$_} =~ s/&quot;/"/g;
		$$in{$_} =~ s/&#39;/'/g;
		$$in{$_} =~ s/&amp;/&/g;

		# 本文内容
		my $tmp;
#		if ($$in{$_} =~ /\n/) {
#			$tmp = "$key_name = \n$$in{$_}\n";
#		} else {
#			$tmp = "$key_name = $$in{$_}\n";
#		}
		#2015.2.15 レイアウト改善
		$tmp = "◆$key_name\n$$in{$_}\n\n";

		$mbody .= $tmp;

		$bef = $_;

		#2015.2.15 key_name＝会社 の場合、問合せ人の会社を変数に格納
		if ($key_name =~ '会社') {
			$inquirerCom = $$in{$_};
		}

		#2015.2.15 key_name＝お名前 の場合、問合せ人の名前を変数に格納
		if ($key_name =~ 'お名前') {
			$inquirerNm = $$in{$_};
		}

	}
	# コード変換
#	$mbody = $j->set(\$mbody,'utf8')->jis;
	$mbody = $j->set(\$mbody,'utf8')->utf8;

	# 本文テンプレ内の変数を置き換え
	$tbody =~ s/!message!/$mbody/;
	# 2015.2.15 本文テンプレ内の問合せ人の会社を置き換え
	$tbody =~ s/!inquirerCom!/$inquirerCom/;
	# 2015.2.15 本文テンプレ内の問合せ人の名前を置き換え
	$tbody =~ s/!inquirerNm!/$inquirerNm/;
	# 2015.2.15 本文テンプレ内の問合せ受理担当のメアドを置き換え
	$tbody =~ s/!inquireeEmail!/$cf{mailto}/;

	# 返信テンプレ内の変数を置き換え
	$resbody =~ s/!message!/$mbody/ if ($cf{auto_res});
	# 2015.2.15 返信テンプレ内の問合せ人の会社を置き換え
	$resbody =~ s/!inquirerCom!/$inquirerCom/ if ($cf{auto_res});
	# 2015.2.15 返信テンプレ内の問合せ人の名前を置き換え
	$resbody =~ s/!inquirerNm!/$inquirerNm/ if ($cf{auto_res});
	# 2015.2.15 返信テンプレ内の問合せ受理担当のメアドを置き換え
	$resbody =~ s/!inquireeEmail!/$cf{mailto}/ if ($cf{auto_res});

	# メールアドレスがない場合は送信先に置き換え
	my $email = $$in{email} eq '' ? $cf{mailto} : $$in{email};

	# MIMEエンコード
	my $sub_me = $$in{subject} ne '' && defined($cf{multi_sub}->{$$in{subject}}) ? $cf{multi_sub}->{$$in{subject}} : $cf{subject};
	$sub_me = $j->set($sub_me,'utf8')->mime_encode;
	my $from;
	if ($$in{name}) {
		$$in{name} =~ s/[\r\n]//g;
		$from = $j->set("\"$$in{name}\" <$email>",'utf8')->mime_encode;
	} else {
		$from = $email;
	}

	# --- 送信内容フォーマット開始
	# ヘッダー
	my $body = "To: $cf{mailto}\n";
	$body .= "From: $from\n";
	$body .= "Subject: $sub_me\n";
	$body .= "MIME-Version: 1.0\n";
	$body .= "Date: $date2\n";
#	$body .= "Content-type: text/plain; charset=iso-2022-jp\n";
#	$body .= "Content-Transfer-Encoding: 7bit\n";
	$body .= "Content-type: text/plain; charset=utf-8\n";
	$body .= "Content-Transfer-Encoding: 8bit\n";
	$body .= "X-Mailer: $cf{version}\n\n";
	$body .= "$tbody\n";

	# 返信内容フォーマット
	my $res_body;
	if ($cf{auto_res}) {

		# 件名MIMEエンコード
		my $re_sub = Jcode->new($cf{sub_reply})->mime_encode;

		$res_body .= "To: $email\n";
		$res_body .= "From: $cf{mailto}\n";
		$res_body .= "Subject: $re_sub\n";
		$res_body .= "MIME-Version: 1.0\n";
#		$res_body .= "Content-type: text/plain; charset=iso-2022-jp\n";
#		$res_body .= "Content-Transfer-Encoding: 7bit\n";
		$res_body .= "Content-type: text/plain; charset=utf-8\n";
		$res_body .= "Content-Transfer-Encoding: 8bit\n";
		$res_body .= "Date: $date2\n";
		$res_body .= "X-Mailer: $cf{version}\n\n";
		$res_body .= "$resbody\n";
	}

	# senmdailコマンド
	my $scmd = $cf{sendmail};
	if ($cf{send_fcmd}) {
		$scmd .= " -f $from";
	}

	# 本文送信
	open(MAIL,"| $scmd -t -i") or &error("メール送信失敗");
	print MAIL "$body\n";
	close(MAIL);

	# 返信送信
	if ($cf{auto_res}) {
		my $scmd = $cf{sendmail};
		if ($cf{send_fcmd}) {
			$scmd .= " -f $cf{mailto}";
		}
		open(MAIL,"| $scmd -t -i") or &error("メール送信失敗");
		print MAIL "$res_body\n";
		close(MAIL);
	}

	# リロード
	if ($cf{reload}) {
		if ($ENV{PERLXS} eq "PerlIS") {
			print "HTTP/1.0 302 Temporary Redirection\r\n";
			print "Content-type: text/html\n";
		}
		print "Location: $cf{back}\n\n";
		exit;

	# 完了メッセージ
	} else {
		open(IN,"$cf{tmpldir}/thx.html") or &error("open err: thx.html");
		my $tmpl = join('', <IN>);
		close(IN);

		# 表示
		print "Content-type: text/html\n\n";
		$tmpl =~ s/!back!/$cf{back}/g;
		&footer($tmpl);
	}
}

#-----------------------------------------------------------
#  入力エラー表示
#-----------------------------------------------------------
sub err_check {
	my $match2 = shift;

	# テンプレート読み込み
	my ($err,$flg,$cell,%fname,%err);
	open(IN,"$cf{tmpldir}/err2.html") or &error("open err: err2.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# テンプレート分割
	my ($head,$loop,$foot);
	if ($tmpl =~ /(.+)<!-- cell_begin -->(.+)<!-- cell_end -->(.+)/s) {
		($head,$loop,$foot) = ($1,$2,$3);
	} else {
		&error("テンプレートが不正です");
	}

	# ヘッダ
	print "Content-type: text/html\n\n";
	print $head;

	# 内容展開
	my $bef;
	foreach my $key (@$key) {
		next if ($key eq "need");
		next if ($key eq "match");
		next if ($$in{match} && $key eq $match2);
		next if ($bef eq $key);
		next if ($key eq "x");
		next if ($key eq "y");
		next if ($key eq "subject");

		my $key_name = defined($cf{replace}->{$key}) ? $cf{replace}->{$key} : $key;
		my $tmp = $loop;
		$tmp =~ s/!key!/$key_name/;

		my $erflg;
		foreach my $err (@err) {
			if ($err eq $key) {
				$erflg++;
				last;
			}
		}
		# 入力なし
		if ($erflg) {
			# $tmp =~ s/!val!/<span class="msg">$key_nameは入力必須です.<\/span>/;
			# 2015.3.15
			# $tmp =~ s/!val!/<span class="msgError">$key_nameは入力必須です.<\/span>/;
			# 2015.3.22
			$tmp =~ s/!val!/<span class="msgError">未入力<\/span>/;
			
		# 正常
		} else {
			$$in{$key} =~ s/\t/<br \/>/g;
			$tmp =~ s/!val!/$$in{$key}/;
		}
		print $tmp;

		$bef = $key;
	}

	# フッタ
	print $foot;
	exit;
}

#-----------------------------------------------------------
#  フォームデコード
#-----------------------------------------------------------
sub parse_form {
	my (@key,@need,%in);
	foreach my $key ( $cgi->param() ) {

		# 複数値の場合はスペースで区切る
		my $val = join(" ", $cgi->param($key));

		# 無害化/改行変換
		$key =~ s/[<>&"'\r\n]//g;
		$val =~ s/&/&amp;/g;
		$val =~ s/</&lt;/g;
		$val =~ s/>/&gt;/g;
		$val =~ s/"/&quot;/g;
		$val =~ s/'/&#39;/g;
		$val =~ s/\r\n/\t/g;
		$val =~ s/\r/\t/g;
		$val =~ s/\n/\t/g;

		# 文字コード変換
		if ($cf{conv_code}) {
			$key = $j->set($key)->utf8;
			$val = $j->set($val)->utf8;
		}

		# 入力必須
		if ($key =~ /^_(.+)/) {
			$key = $1;
			push(@need,$key);
		}

		# 受け取るキーの順番を覚えておく
		push(@key,$key);

		# %inハッシュに代入
		$in{$key} = $val;
	}

	# post送信チェック
	if ($cf{postonly} && $ENV{REQUEST_METHOD} ne 'POST') {
		&error("不正なアクセスです");
	}

	# リファレンスで返す
	return (\@key, \@need, \%in);
}

#-----------------------------------------------------------
#  フッター
#-----------------------------------------------------------
sub footer {
	my $foot = shift;

	# 著作権表記（削除・改変禁止）
	my $copy = <<EOM;
<p style="margin-top:2em;text-align:center;font-family:Verdana,Helvetica,Arial;font-size:10px;">
- <a href="http://www.kent-web.com/" target="_top">POST MAIL</a> -
</p>
EOM

	if ($foot =~ /(.+)(<\/body[^>]*>.*)/si) {
		print "$1$copy$2\n";
	} else {
		print "$foot$copy\n";
		print "<body></html>\n";
	}
	exit;
}

#-----------------------------------------------------------
#  エラー処理
#-----------------------------------------------------------
sub error {
	my $err = shift;

	open(IN,"$cf{tmpldir}/err1.html") or &error("open err: err1.html");
	my $tmpl = join('', <IN>);
	close(IN);

	# 文字置き換え
	$tmpl =~ s/!error!/$err/g;

	print "Content-type: text/html\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  時間取得
#-----------------------------------------------------------
sub get_time {
	$ENV{TZ} = "JST-9";
	my ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime(time);
	my @week  = qw|Sun Mon Tue Wed Thu Fri Sat|;
	my @month = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;

	# 日時のフォーマット
	my $date1 = sprintf("%04d/%02d/%02d(%s) %02d:%02d:%02d",
			$year+1900,$mon+1,$mday,$week[$wday],$hour,$min,$sec);
	my $date2 = sprintf("%s, %02d %s %04d %02d:%02d:%02d",
			$week[$wday],$mday,$month[$mon],$year+1900,$hour,$min,$sec) . " +0900";

	return ($date1,$date2);
}

#-----------------------------------------------------------
#  ホスト名取得
#-----------------------------------------------------------
sub get_host {
	# ホスト名取得
	my $h = $ENV{REMOTE_HOST};
	my $a = $ENV{REMOTE_ADDR};

	if ($cf{gethostbyaddr} && ($h eq "" || $h eq $a)) {
		$h = gethostbyaddr(pack("C4", split(/\./, $a)), 2);
	}
	if ($h eq "") { $h = $a; }

	# チェック
	if ($cf{denyhost}) {
		my $flg;
		foreach ( split(/\s+/, $cf{denyhost}) ) {
			s/\./\\\./g;
			s/\*/\.\*/g;

			if ($h =~ /$_/i) { $flg++; last; }
		}
		if ($flg) { &error("アクセスを許可されていません"); }
	}

	return ($h,$a);
}

#-----------------------------------------------------------
#  送信チェック
#-----------------------------------------------------------
sub check_post {
	my $job = shift;

	# 時間取得
	my $now = time;

	# ログオープン
	open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
	eval "flock(DAT, 2);";
	my $data = <DAT>;

	# 分解
	my ($ip,$time) = split(/<>/, $data);

	# IP及び時間をチェック
	if ($ip eq $addr && $now - $time <= $cf{block_post}) {
		close(DAT);
		&error("連続送信は$cf{block_post}秒間お待ちください");
	}

	# 送信時は保存
	if ($job eq "send") {
		seek(DAT, 0, 0);
		print DAT "$addr<>$now";
		truncate(DAT, tell(DAT));
	}
	close(DAT);
}


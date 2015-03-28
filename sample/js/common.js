/* ===================================================================

 * ページトップへの戻り

=================================================================== */
$(function(){
    // スクロールすると表示するエリア
    var element = $('#pageTop');
    // スクロール量の設定
    var position = 400; // 単位：px
    // スクロールすると表示するエリアを非表示
    element.hide();
    $(window).scroll(function(){
        // スクロールすると表示させる
        if ($(this).scrollTop() > position) {
            $(element).fadeIn();
        } else {
            $(element).fadeOut();
        }
    });
});


/* ===================================================================

 * スムーススクロール

=================================================================== */
$(function(){
    // #で始まるアンカーをクリックした場合に処理
    $('a[href^=#]').click(function() {
        // スクロールの速度
        var duration = 400;// ミリ秒
        // アンカーの値取得
        var href= $(this).attr("href");
        // 移動先を取得
        var target = $(href == "#" || href == "" ? 'html' : href);
        // 移動先を数値で取得
        var position = target.offset().top;
        // スムーススクロール
        $('body,html').animate({scrollTop:position}, duration, 'swing');
        return false;
    });
});


/* ===================================================================

 * スライドショー

=================================================================== */
$.fn.slideshow = function(options) {
    // オプション
    var o = $.extend({
        autoSlide    : true,
        effect       : 'fade',
        type         : 'repaet',
        interval     : 3000,
        duration     : 1000,
        imgHoverStop : true,
        navHoverStop : true
    }, options);

    // セレクター
    var $slider      = $(this),
         $container  = $slider.find('.slideInner'),
         $element    = $container.children(),
         $prevNav    = $slider.find('.slidePrev'),
         $nextNav    = $slider.find('.slideNext'),
         $controlNav = $slider.find('.controlNav');

    // カウンター初期化
    var current = 0;
    var next = 1;

    // PREV/NEXTフラグ
    var flag = 'nextElement';

    // ストップフラグ
    var stopFlag = false;

    // 全ての要素を非表示にする
    $element.hide();

    // 最初の要素だけ表示する
    $($element[0]).show();

    // 読み込み時に要素の高さを取得
    $(window).on('load resize', function(){
        elementHeight();
    });

    // 画像の高さ分、表示領域を確保
    var elementHeight = function(){
        $container.height($element.height());
    };

    // 自動切り替えスタート
    var start;
    var startTimer = function () {
        start = setInterval(function(){change();}, o.interval);
    };

    // 自動切り替えストップ
    var stopTimer = function () {
         clearInterval(start);
    };

    // アニメーション時無効化
    var clear = function () {
        if($element.is(':animated')) { return false; }
   };

    if (o.type == 'stop') {
        $prevNav.hide();
    }

    // 要素を切り替えるスクリプト
    var change = function(){

        // アニメーション時無効化
        clear();

        // PREV/NEXTボタンデザイン
        if (o.type == 'stop') {
            if(next > 0){
                $prevNav.fadeIn('slow');
            }else{
                $prevNav.fadeOut('slow');
            }
        }

        // コントールナビデザイン
        $controlNav.children('span').removeClass('current');
        $controlNav.children('span:eq(' + next + ')').addClass('current');

        // フェードしながら切り替える場合
        if (o.effect == 'fade') {
            $($element[current]).not(':animated').fadeOut(o.duration);
            $($element[next]).not(':animated').fadeIn(o.duration);

        // スライドしながら切り替える場合
        } else if  (o.effect == 'slide') {
            var elementWidth = $container.width();
            $element.css('display', 'block');
            $element.css('width', elementWidth +'px');
            if(flag == 'prevElement') {
                $element.css('left', - elementWidth +'px');
                $($element[current]).css('left', 0 +'px');
                $($element[current]).not(':animated').animate({'left': '+=' + elementWidth +'px'}, o.duration);
                $($element[next]).not(':animated').animate({'left': '+=' + elementWidth +'px'}, o.duration);
            }
            if(flag == 'nextElement') {
                $element.css('left', elementWidth +'px');
                $($element[current]).css('left', 0 +'px');
                $($element[current]).not(':animated').animate({'left': '-=' + elementWidth +'px'}, o.duration);
                $($element[next]).not(':animated').animate({'left': '-=' + elementWidth +'px'}, o.duration);
            }
        }

        // リピートする場合
        if (o.type == 'repeat') {
            if ((next + 1) < $element.length) {
                 current = next;
                 next++;
            } else {
                 current = $element.length - 1;
                 next = 0;
            }
        }

        // 最後の要素でストップする場合
        if (o.type == 'stop') {
            if ((next + 1) < $element.length) {
                current = next;
                next++;
                $nextNav.fadeIn();
            } else {
                current = $element.length - 1;
                next = 0;
                stopTimer();
                $nextNav.fadeOut();
                stopFlag = true;
          }
        }

    };

    // PREVボタン
    var prevSlide = function () {
        clear();
        flag = 'prevElement';
        if(current == 0) {
            next = $element.length - 1;
        }else {
            next = current -1;
        }
        stopTimer();
        change();
        startTimer();
        flag = 'nextElement';
    }

    // NEXTボタン
    var nextSlide = function () {
        clear();
        flag = 'nextElement';
        stopTimer();
        change();
        startTimer();
    }

    // PREVスライド
    $prevNav.click(function(){
        prevSlide();
        stopTimer();
    });

    // NEXTスライド
    $nextNav.click(function(){
        nextSlide();
        stopTimer();
    });

    // コントローラーの生成
    $element.each(function (i) {
        $('<span/>').text(i + 1).appendTo($controlNav)
        .click(function () {
            clear();
            if(i < current) {
                flag='prevElement';
            } else if(i > current) {
                flag='nextElement';
            }
            if(i != current) {
                if(o.type == 'repeat'){
                    stopTimer();
                }
                if(i == $element.length) {
                    next = 0;
                }else {
                    next = i;
                }
                change();
                if(o.type == 'repeat'){
                    startTimer();
                }
                flag = 'nextElement';
            }
            stopTimer();
        });
    });
    $controlNav.find('span:first-child').addClass('current');

    // ホバー時に画像静止（自動切り替えストップ）
    if(o.imgHoverStop){
        $container.hover(
            function () {
                stopTimer();
            },
            function () {
                if(stopFlag || !o.autoSlide) {
                    stopTimer();
                }else {
                    startTimer();
                }
            }
        );
    }

    // ナビゲーションのホバー動作
    if(o.navHoverStop){
        $prevNav.hover(
            function () {
                stopTimer();
            },
            function () {
                if(stopFlag || !o.autoSlide) {
                    stopTimer();
                }else {
                    startTimer();
                }
            }
        );
        $nextNav.hover(
            function () {
                stopTimer();
            },
            function () {
                if(stopFlag || !o.autoSlide) {
                    stopTimer();
                }else {
                    startTimer();
                }
            }
        );
        $controlNav.hover(
            function () {
                stopTimer();
            },
            function () {
                if(stopFlag || !o.autoSlide) {
                    stopTimer();
                }else {
                    startTimer();
                }
            }
        );
    }

    // 自動スタート設定
    if(o.autoSlide){
        startTimer();
    }

};


/* ===================================================================

 * コンテンツの高さを揃える

=================================================================== */
$.fn.uniformHeight = function() {
    var maxHeight = 0;
    this.each(function() {
        var thisHeight = $(this).height();
        if(thisHeight > maxHeight){
            maxHeight = thisHeight;
        }
    });
    $(this).height(maxHeight);
};
========================================================
Pythonスクリプトで拡張可能な2画面ファイラ [ 内骨格 ]
========================================================

:著作者: craftware
:連絡先: craftware@gmail.com
:種別: フリーウェア
:動作環境: Windows 7/8/10
:Webサイト: http://sites.google.com/site/craftware/


使い方
=========================

    使い方については、doc/index.html を参照してください。


ビルド方法
=========================

    必要なレポジトリをチェックアウト

        cfiler
        ckit
        pyauto

    Python (32bit版) を c:/Python37 にインストール

    Pillow をインストール::

        pip install pillow

    VisualStudio 2015 で、Native モジュールをビルド

        ckit/ckitcore/ckitcore.sln
        pyauto/pyauto.sln
        cfiler/cfiler_native/cfiler_native.sln
        cfiler/cfiler.sln

    デバッグ実行 (cmd.exe などで下記を実行)::

        cfiler_d.exe -d

    リリースパッケージビルド::

        python makefile.py



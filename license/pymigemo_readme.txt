PyMigemo 0.1
============
Atzm WATANABE (10/12/'05)

これは何？
----------
C/Migemo を Python から使うためのラッパーです．

必要なもの
----------
C/Migemo ライブラリがインストールされていることが
前提となっています．ライブラリ検索パスに migemo.so
が，ヘッダ検索パスに migemo.h が存在することを確認
して下さい．

インストール方法
----------------
同梱の setup.py を利用して下さい．

 $ ./setup.py build
 # ./setup.py install

ライセンス
----------
FreeBSD スタイルライセンスに準拠します．

使い方
------
Python インタプリタ上で migemo を import して下さい．

リファレンス
- - - - - - -
モジュールコンテンツ
 * VERSION
    ** MIGEMO_VERSION
        C/Migemo のバージョン

    ** PYMIGEMO_VERSION
        PyMigemo のバージョン

 * DICTID
    後述の load メソッドで使う辞書 ID．

    ** DICTID_MIGEMO
        migemo-dict 辞書

    ** DICTID_ROMA2HIRA
        ローマ字→平仮名変換表

    ** DICTID_HIRA2KATA
        平仮名→カタカナ変換表

    ** DICTID_HAN2ZEN
        半角→全角変換表

    ** DICTID_ZEN2HAN
        全角→半角変換表

    ** DICTID_INVALID
        load メソッドで辞書の読み込みに失敗した場合に返る

 * OPINDEX
    後述の Migemo.set_operator，Migemo.get_operator メソッドで使う
    インデクス．

    ** OPINDEX_OR
        論理和．デフォルトは "|"

    ** OPINDEX_NEST_IN
        グルーピング時の開き括弧．
        Migemo.get_operator() に渡した際のデフォルトは "("

    ** OPINDEX_NEST_OUT
        グルーピング時の閉じ括弧．
        Migemo.get_operator() に渡した際のデフォルトは ")"

    ** OPINDEX_SELECT_IN
        選択の開始を表す開き鈎括弧．
        Migemo.get_operator() に渡した際のデフォルトは "["

    ** OPINDEX_SELECT_OUT
        選択の終了を表す閉じ鈎括弧．
        Migemo.get_operator() に渡した際のデフォルトは "]"

    ** OPINDEX_NEWLINE
        各文字の間に挿入される「0 個以上の空白もしくは改行にマッチする」
        パターン．
        Migemo.get_operator() に渡した際のデフォルトは "" (空文字列)

 * Migemo クラス
    ** __init__(dictionary)
        Migemo クラスのコンストラクタ．
        *** 引数
             dictionary: migemo-dict 辞書ファイルのパス (str)

    ** get_encoding()
        migemo-dict 辞書のエンコーディングを str で返す．
        例えば EUC-JP で書かれた辞書であれば "euc_jp" が返る．
        cp932，euc_jp，utf8 のいずれかを返すが，辞書のエンコーディングがこ
        れらに該当しなかった場合はファイルシステムのデフォルトエンコーディ
        ングを返す．
        *** 引数
             なし
        *** 返り値
             エンコーディング文字列 (str)

    ** get_operator(index)
        index で指定された，正規表現に使用するメタ文字を返す (str)．
        *** 引数
             index: 前述の OPINDEX のいずれか
        *** 返り値
             メタ文字列 (str)

    ** is_enable()
        Migemo 内部に，正常に辞書が読み込めているかどうかをチェックする．
        *** 引数
             なし
        *** 返り値
             真偽値 (int) : 正常に読み込めている場合に真

    ** load(dict_id, dict_file)
        Migemo オブジェクトに辞書を追加で読み込む．
        *** 引数
             dict_id: 前述の DICTID のいずれか
             dict_file: 辞書ファイルのパス
        *** 返り値
             読み込んだ辞書の DICTID．
             読み込みに失敗した場合 DICTID_INVALID が返る．

    ** query(query)
        query で与えられた文字列から日本語検索のための正規表現を返す．
        *** 引数
             query: 問い合わせる文字列 (Unicode or str)
                    str で ascii 以外の文字列を渡す場合，辞書と同じエン
                    コーディングの文字列でないとエラーになる可能性がある．
        *** 返り値
             正規表現文字列 (Unicode)

    ** set_operator(index, op)
        index で指定された，正規表現に使用するメタ文字を op に変更する．
        *** 引数
             index: 前述の OPINDEX のいずれか
             op: メタ文字列 (str)
        *** 返り値
             真偽値 (int) : 成功時に真

作者
----
Atzm WATANABE <sitosito@p.chan.ne.jp>

本ソフトウェアに対するコメント，バグ報告，パッチなどは大いに歓迎
します．上記のメールアドレスまでお気軽にお寄せ下さい．

$Id: README.ja,v 1.2 2005/10/12 15:15:04 atzm Exp $

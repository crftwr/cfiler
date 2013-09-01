## @addtogroup error
## @{

## 内骨格の独自定義のエラーのベースクラス
class Error( Exception ):
    pass

## 要求されたアイテムやリソースが存在しなかったというエラー
class NotExistError( Error ):
    pass

## 操作がキャンセルされたというエラー
class CanceledError( Error ):
    pass

## @} error

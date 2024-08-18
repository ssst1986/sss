from django.shortcuts import render
import glob
from datetime import datetime
# Create your views here.

def show_template(request, date_str):
    """
    指定された日付のテンプレートを表示する
    """
    # 日付文字列をdatetimeオブジェクトに変換
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # 日付の形式が正しくない場合、エラーページを表示
        return render(request, 'Mappa/error.html', {'message': 'Invalid date format'})

    # テンプレート名を生成
    template_name = f'Mappa/{date_str}.html'

    # テンプレートをレンダリング
    return render(request, template_name)


def select_template(request):
    """
    日付を選択するためのビュー
    """
    # 利用可能な日付のリストを作成
    #available_dates = ['2023-08-15','2023-08-16','2023-08-17',]

    #result = glob.glob(r"C:\Users\Owner\Desktop\virtual\my_project\Mappa\templates\Mappa\202*.html")
    result = glob.glob("/home/st1986/st1986.pythonanywhere.com/Mappa/templates/Mappa/202*.html")
    def splitmap(x):
        y = x.split('templates/Mappa/')[-1].split('.')[0]
        return y

    available_dates = list(map(splitmap,result))

    return render(request, 'Mappa/select_template.html', {'available_dates': available_dates})


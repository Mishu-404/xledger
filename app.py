from flask import Flask, request, send_file, render_template
import pandas as pd, os, io
from datetime import datetime, timezone, timedelta, date
from collections import OrderedDict

app = Flask(__name__)

BN_TR = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
BN_MONTHS = ["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন",
             "জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"]

def bn(n):    return str(n).translate(BN_TR)
def fmt(n):   return "{:,}".format(abs(int(n)))
def fmtbn(n): return bn(fmt(n))

def bn_date(date_str):
    try:
        parts = date_str.replace('/', '-').split('-')
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        if y >= 100: y = y % 100
        return "{} {} {}".format(bn(d), BN_MONTHS[m-1], bn(y))
    except:
        return date_str

def now_bst():
    bst = datetime.now(timezone.utc) + timedelta(hours=6)
    return "{} {} {}  |  {}:{}".format(
        bn(bst.day), BN_MONTHS[bst.month-1], bn(bst.year),
        bn(bst.strftime('%H')), bn(bst.strftime('%M')))

def get_font_css():
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'kalpurush.ttf'),
        '/opt/render/project/src/static/kalpurush.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            url = 'file://' + p
            return "@font-face { font-family: 'Kalpurush'; src: url(" + url + ") format('truetype'); }"
    return ""

def parse_trips(file_obj):
    df = pd.read_excel(file_obj, sheet_name=0, header=None)
    trips = []
    for row in df.values.tolist():
        try:
            sn = int(float(str(row[0])))
            if sn < 1 or sn > 500: continue
        except: continue
        date_raw = row[1]
        if hasattr(date_raw, 'strftime'):
            date_str = date_raw.strftime('%d-%m-%y')
        else:
            s = str(date_raw)
            date_str = s[:10] if s != 'nan' else ''
        def safe(v):
            try: return round(float(str(v))) if str(v) != 'nan' else 0
            except: return 0
        bill=safe(row[12]); fare=safe(row[14]); vat=safe(row[15])
        cof=safe(row[17]); profit=safe(row[18]); sqft=safe(row[10])
        if not bill and not fare: continue
        trips.append({
            'n': sn, 'date': date_str,
            'truck':  str(row[2]) if str(row[2]) != 'nan' else '',
            'dealer': str(row[4]) if str(row[4]) != 'nan' else '',
            'dest':   str(row[6]) if str(row[6]) != 'nan' else '',
            'sqft': sqft, 'bill': bill, 'fare': fare,
            'vat': vat, 'cof': cof, 'profit': profit
        })
    return trips

def td(text, color='', bold=False, align='center', bg='', size=12):
    s = 'padding:6px 9px;font-size:{}px;text-align:{};border:1px solid #C8DCF0;'.format(size, align)
    if bg:    s += 'background:{};'.format(bg)
    if color: s += 'color:{};'.format(color)
    if bold:  s += 'font-weight:700;'
    return '<td style="{}">{}</td>'.format(s, text)

def th(text, align='center', width=''):
    w = 'width:{};'.format(width) if width else ''
    s = 'background:#3B7DD8;color:#fff;padding:7px 9px;font-size:12px;text-align:{};border:1px solid #2A6DC8;white-space:nowrap;{}'.format(align, w)
    return '<th style="{}">{}</th>'.format(s, text)

def alt(i): return '#EBF4FF' if i % 2 == 0 else '#FFFFFF'
TS = 'padding:7px 9px;border:1px solid #C8DCF0;'

def build_html(trips, company, provider):
    tBill   = sum(t['bill']   for t in trips)
    tFare   = sum(t['fare']   for t in trips)
    tVAT    = sum(t['vat']    for t in trips)
    tCOF    = sum(t['cof']    for t in trips)
    tProfit = sum(t['profit'] for t in trips)
    tc  = '#1A7A3C' if tProfit >= 0 else '#C0392B'
    tsg = '-' if tProfit < 0 else ''

    daily = OrderedDict()
    for t in trips:
        d = t['date']
        if d not in daily:
            daily[d] = {'cnt': 0, 'bill': 0, 'fare': 0, 'vatcof': 0, 'profit': 0}
        daily[d]['cnt']    += 1
        daily[d]['bill']   += t['bill']
        daily[d]['fare']   += t['fare']
        daily[d]['vatcof'] += t['vat'] + t['cof']
        daily[d]['profit'] += t['profit']

    s1 = ''
    for i, (lbl, val, col, note) in enumerate([
        ('মোট বিল (Total Bill)',     tBill,   '#1A5276', '{} যাত্রার মোট বিল'.format(bn(len(trips)))),
        ('মোট ভাড়া (Total Fare)',    tFare,   '#2A9D8F', 'পরিশোধিত ভাড়া'),
        ('ভ্যাট ও এআইটি (৫% Fare)', tVAT,    '#B7770D', 'ভাড়ার ৫%'),
        ('সিওএফ (COF 15%/60d)',      tCOF,    '#6C3483', 'অর্থায়ন খরচ'),
        ('নেট লাভ',                  tProfit, tc,        'সকল খরচ বাদে'),
    ]):
        sg = '-' if val < 0 else ''
        s1 += '<tr>' + td(bn(i+1), bg=alt(i)) + td(lbl, align='left', bg=alt(i)) + \
              td(sg+'৳ '+fmtbn(abs(val)), color=col, bold=True, align='right', bg=alt(i)) + \
              td(note, bg=alt(i), size=11) + '</tr>'

    s2 = ''
    for i, (d, v) in enumerate(daily.items()):
        pc = '#1A7A3C' if v['profit'] >= 0 else '#C0392B'
        sg = '-' if v['profit'] < 0 else ''
        s2 += '<tr>' + td(bn_date(d), bg=alt(i), size=11) + td(bn(v['cnt'])+'টি', bg=alt(i)) + \
              td('৳ '+fmtbn(v['bill']),   color='#1A5276', bold=True, align='right', bg=alt(i)) + \
              td('৳ '+fmtbn(v['fare']),   color='#2A9D8F', align='right', bg=alt(i)) + \
              td('৳ '+fmtbn(v['vatcof']), color='#B7770D', align='right', bg=alt(i)) + \
              td(sg+'৳ '+fmtbn(abs(v['profit'])), color=pc, bold=True, align='right', bg=alt(i)) + '</tr>'
    s2 += ('<tr style="background:#D6E8FA;font-weight:700;">'
           '<td style="' + TS + '">মোট</td>'
           '<td style="' + TS + 'text-align:center;">' + bn(len(trips)) + 'টি</td>'
           '<td style="' + TS + 'text-align:right;color:#1A5276;">৳ ' + fmtbn(tBill) + '</td>'
           '<td style="' + TS + 'text-align:right;color:#2A9D8F;">৳ ' + fmtbn(tFare) + '</td>'
           '<td style="' + TS + 'text-align:right;color:#B7770D;">৳ ' + fmtbn(tVAT+tCOF) + '</td>'
           '<td style="' + TS + 'text-align:right;color:' + tc + ';font-weight:700;">' + tsg + '৳ ' + fmtbn(abs(tProfit)) + '</td>'
           '</tr>')

    s3 = ''
    for i, t in enumerate(trips):
        vc = t['vat'] + t['cof']
        pc = '#1A7A3C' if t['profit'] >= 0 else '#C0392B'
        sg = '-' if t['profit'] < 0 else ''
        s3 += '<tr>' + \
              td(bn(t['n']), bg=alt(i)) + \
              td(bn_date(t['date']), bg=alt(i), size=11) + \
              td(t['truck'],  bg=alt(i), size=10) + \
              td(t['dealer'], align='left', bg=alt(i), size=11) + \
              td(t['dest'],   bg=alt(i), size=11) + \
              td(fmtbn(t['sqft']), align='right', bold=True, bg=alt(i), size=11) + \
              td('৳ '+fmtbn(t['bill']),  color='#1A5276', bold=True, align='right', bg=alt(i), size=11) + \
              td('৳ '+fmtbn(t['fare']),  color='#2A9D8F', bold=True, align='right', bg=alt(i), size=11) + \
              td('৳ '+fmtbn(vc),         color='#B7770D', bold=True, align='right', bg=alt(i), size=11) + \
              td(sg+'৳ '+fmtbn(abs(t['profit'])), color=pc, bold=True, align='right', bg=alt(i), size=11) + \
              '</tr>'
    s3 += ('<tr style="background:#D6E8FA;font-weight:700;">'
           '<td style="' + TS + '">মোট</td>'
           '<td colspan="5" style="' + TS + '"></td>'
           '<td style="' + TS + 'text-align:right;color:#1A5276;">৳ ' + fmtbn(tBill) + '</td>'
           '<td style="' + TS + 'text-align:right;color:#2A9D8F;">৳ ' + fmtbn(tFare) + '</td>'
           '<td style="' + TS + 'text-align:right;color:#B7770D;">৳ ' + fmtbn(tVAT+tCOF) + '</td>'
           '<td style="' + TS + 'text-align:right;color:' + tc + ';font-weight:700;">' + tsg + '৳ ' + fmtbn(abs(tProfit)) + '</td>'
           '</tr>')

    font_css = get_font_css()

    return (
        '<!DOCTYPE html><html lang="bn"><head><meta charset="UTF-8"><style>'
        + font_css +
        ' @page { size: A4; margin: 13mm; }'
        ' * { box-sizing: border-box; margin: 0; padding: 0; }'
        " body { font-family: 'Kalpurush', sans-serif; color: #1A2E4A; font-size: 13px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }"
        ' h2 { font-size: 15px; font-weight: 700; color: #1A2E4A; margin: 14px 0 6px; padding-bottom: 4px; border-bottom: 3px solid #3B7DD8; }'
        ' table { width: 100%; border-collapse: collapse; margin-bottom: 2px; }'
        ' .footer { margin-top: 18px; padding-top: 7px; border-top: 1px solid #D0DEF0; display: flex; justify-content: space-between; }'
        '</style></head><body>'
        '<div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:7px;border-bottom:3px solid #3B7DD8;margin-bottom:9px">'
        '<div style="font-size:20px;font-weight:700">' + company + '</div>'
        '<div style="font-size:11px;color:#7A9ABF;">পরিবহন বিল লগ</div></div>'
        '<div style="text-align:center;font-size:19px;font-weight:700;margin-bottom:4px">পরিবহন বিল লগ — প্রতিবেদন</div>'
        '<div style="text-align:center;font-size:12px;color:#4A6A8A;margin-bottom:3px">মোট যাত্রা: ' + bn(len(trips)) + 'টি &nbsp;|&nbsp; মোট বিল: ৳' + fmtbn(tBill) + ' &nbsp;|&nbsp; নেট লাভ: <span style="color:' + tc + ';font-weight:700;">' + tsg + '৳' + fmtbn(abs(tProfit)) + '</span></div>'
        '<div style="text-align:center;font-size:11px;color:#9EAFC0;margin-bottom:14px;padding-bottom:6px;border-bottom:1px solid #E0EAFA">রিপোর্ট তৈরির সময়ঃ &nbsp;' + now_bst() + '&nbsp; (স্বয়ংক্রিয়ভাবে তৈরি)</div>'
        '<h2>১.&nbsp; মোট আর্থিক সারসংক্ষেপ</h2>'
        '<table><thead><tr>' + th('ক্র.','center','40px') + th('বিবরণ','left') + th('পরিমাণ (টাকা)','right','150px') + th('মন্তব্য','left','160px') + '</tr></thead><tbody>' + s1 + '</tbody></table>'
        '<h2>২.&nbsp; দৈনিকভিত্তিক বিবরণ</h2>'
        '<table><thead><tr>' + th('তারিখ') + th('যাত্রা','center','50px') + th('মোট বিল (৳)','right') + th('মোট ভাড়া (৳)','right') + th('ভ্যাট+COF (৳)','right') + th('নেট লাভ (৳)','right') + '</tr></thead><tbody>' + s2 + '</tbody></table>'
        '<h2>৩.&nbsp; সম্পূর্ণ যাত্রা তালিকা</h2>'
        '<table><thead><tr>' + th('ক্র.','center','28px') + th('তারিখ','center','62px') + th('ট্রাক','center','48px') + th('ডিলার','left') + th('গন্তব্য','center','72px') + th('বর্গফুট','right','56px') + th('বিল','right','66px') + th('ভাড়া','right','63px') + th('ভ্যাট-COF','right','68px') + th('লাভ (৳)','right','73px') + '</tr></thead><tbody>' + s3 + '</tbody></table>'
        '<div class="footer">'
        '<div style="font-size:12px;color:#4A6A8A">তথ্য প্রদানকারীঃ &nbsp;<strong style="color:#1A2E4A">' + provider + '</strong></div>'
        '<div style="font-size:10px;color:#C8D8EA;">XLedger v2.0 | by Mishu</div>'
        '</div></body></html>'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'কোনো ফাইল পাওয়া যায়নি', 400
    file     = request.files['file']
    company  = request.form.get('company',  'এক্স সিরামিক')
    provider = request.form.get('provider', 'আরিফুল ইসলাম')
    try:
        trips = parse_trips(file)
        if not trips:
            return 'কোনো ট্রিপ ডেটা পাওয়া যায়নি', 400
        html_content = build_html(trips, company, provider)
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        filename = 'XLedger_Report_{}.pdf'.format(date.today().strftime('%d-%m-%Y'))
        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        return 'ত্রুটি: {}'.format(str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

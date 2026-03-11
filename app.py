from flask import Flask, request, send_file, render_template
import pandas as pd, subprocess, os, io, tempfile
from datetime import datetime, timezone, timedelta
from collections import OrderedDict

app = Flask(__name__)

BN_TR = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
BN_MONTHS = ["জানুয়ারি","ফেব্রুয়ারি","মার্চ","এপ্রিল","মে","জুন",
             "জুলাই","আগস্ট","সেপ্টেম্বর","অক্টোবর","নভেম্বর","ডিসেম্বর"]

def bn(n):    return str(n).translate(BN_TR)
def fmt(n):   return f"{abs(int(n)):,}"
def fmtbn(n): return bn(fmt(n))

def now_bst():
    bst = datetime.now(timezone.utc) + timedelta(hours=6)
    return f"{bn(bst.day)} {BN_MONTHS[bst.month-1]} {bn(bst.year)}  |  {bn(bst.strftime('%H'))}:{bn(bst.strftime('%M'))}"

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
            s = str(date_raw); date_str = s[:10] if s != 'nan' else ''
        def safe(v):
            try: return round(float(str(v))) if str(v) != 'nan' else 0
            except: return 0
        bill=safe(row[12]); fare=safe(row[14]); vat=safe(row[15])
        cof=safe(row[17]); profit=safe(row[18]); sqft=safe(row[10])
        if not bill and not fare: continue
        trips.append({'n':sn,'date':date_str,
            'truck': str(row[2]) if str(row[2])!='nan' else '',
            'dealer':str(row[4]) if str(row[4])!='nan' else '',
            'dest':  str(row[6]) if str(row[6])!='nan' else '',
            'sqft':sqft,'bill':bill,'fare':fare,'vat':vat,'cof':cof,'profit':profit})
    return trips

def build_html(trips, company, provider):
    C = dict(navy='#1A2E4A',sky='#3B7DD8',skyL='#EBF4FF',teal='#2A9D8F',
             green='#1A7A3C',red='#C0392B',blue='#1A5276',gold='#B7770D',
             purple='#6C3483',totalBg='#D6E8FA',white='#FFFFFF',muted='#4A6A8A')

    tBill=sum(t['bill'] for t in trips); tFare=sum(t['fare'] for t in trips)
    tVAT=sum(t['vat'] for t in trips);  tCOF=sum(t['cof'] for t in trips)
    tProfit=sum(t['profit'] for t in trips)

    daily = OrderedDict()
    for t in trips:
        d = t['date']
        if d not in daily: daily[d]={'cnt':0,'bill':0,'fare':0,'vatcof':0,'profit':0}
        daily[d]['cnt']+=1; daily[d]['bill']+=t['bill']; daily[d]['fare']+=t['fare']
        daily[d]['vatcof']+=t['vat']+t['cof']; daily[d]['profit']+=t['profit']

    def alt(i): return C['skyL'] if i%2==0 else C['white']
    def th(txt, align='center', w=''):
        ws = f'width:{w};' if w else ''
        return f'<th style="background:{C["sky"]};color:#fff;padding:7px 9px;font-size:12px;text-align:{align};border:1px solid #2A6DC8;white-space:nowrap;{ws}">{txt}</th>'
    def td(txt, color='', bold=False, align='center', bg='', size=12):
        s=f'padding:6px 9px;font-size:{size}px;text-align:{align};border:1px solid #C8DCF0;'
        if bg: s+=f'background:{bg};'
        if color: s+=f'color:{color};'
        if bold: s+='font-weight:700;'
        return f'<td style="{s}">{txt}</td>'

    s1=''
    for i,(lbl,val,col,note) in enumerate([
        ('মোট বিল (Total Bill)',       tBill,  C['blue'],  f'{bn(len(trips))}টি যাত্রার মোট বিল'),
        ('মোট ভাড়া (Total Fare)',      tFare,  C['teal'],  'পরিশোধিত ভাড়া'),
        ('ভ্যাট ও এআইটি (৫% Fare)',   tVAT,   C['gold'],  'ভাড়ার ৫%'),
        ('সিওএফ (COF 15%/60d)',        tCOF,   C['purple'],'অর্থায়ন খরচ'),
        ('নেট লাভ',                    tProfit,C['green'] if tProfit>=0 else C['red'],'সকল খরচ বাদে'),
    ]):
        sg='-' if val<0 else ''
        s1+=f'<tr>{td(bn(i+1),bg=alt(i))}{td(lbl,align="left",bg=alt(i))}{td(sg+"৳ "+fmtbn(abs(val)),color=col,bold=True,align="right",bg=alt(i))}{td(note,bg=alt(i),size=11)}</tr>\n'

    s2=''
    for i,(date,d) in enumerate(daily.items()):
        sg='-' if d['profit']<0 else ''; pc=C['green'] if d['profit']>=0 else C['red']
        s2+=f'<tr>{td(date,bg=alt(i))}{td(bn(d["cnt"])+"টি",bg=alt(i))}{td("৳ "+fmtbn(d["bill"]),color=C["blue"],bold=True,align="right",bg=alt(i))}{td("৳ "+fmtbn(d["fare"]),color=C["teal"],align="right",bg=alt(i))}{td("৳ "+fmtbn(d["vatcof"]),color=C["gold"],align="right",bg=alt(i))}{td(sg+"৳ "+fmtbn(abs(d["profit"])),color=pc,bold=True,align="right",bg=alt(i))}</tr>\n'
    tc=C['green'] if tProfit>=0 else C['red']; tsg='-' if tProfit<0 else ''
    tot=f'background:{C["totalBg"]};font-weight:700;'
    s2+=f'<tr style="{tot}"><td style="padding:7px 9px;border:1px solid #C8DCF0">মোট</td><td style="padding:7px 9px;border:1px solid #C8DCF0;text-align:center">{bn(len(trips))}টি</td><td style="padding:7px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["blue"]}">৳ {fmtbn(tBill)}</td><td style="padding:7px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["teal"]}">৳ {fmtbn(tFare)}</td><td style="padding:7px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["gold"]}">৳ {fmtbn(tVAT+tCOF)}</td><td style="padding:7px 9px;border:1px solid #C8DCF0;text-align:right;color:{tc}">{tsg}৳ {fmtbn(abs(tProfit))}</td></tr>'

    s3=''
    for i,t in enumerate(trips):
        vc=t['vat']+t['cof']; sg='-' if t['profit']<0 else ''; pc=C['green'] if t['profit']>=0 else C['red']
        s3+=f'<tr>{td(bn(t["n"]),bg=alt(i))}{td(t["date"],bg=alt(i),size=11)}{td(t["truck"],bg=alt(i),size=11)}{td(t["dealer"],align="left",bg=alt(i),size=11)}{td(t["dest"],bg=alt(i),size=11)}{td(fmtbn(t["sqft"]),align="right",bg=alt(i),size=11)}{td("৳ "+fmtbn(t["bill"]),color=C["blue"],bold=True,align="right",bg=alt(i),size=11)}{td("৳ "+fmtbn(t["fare"]),color=C["teal"],align="right",bg=alt(i),size=11)}{td("৳ "+fmtbn(vc),color=C["gold"],align="right",bg=alt(i),size=11)}{td(sg+"৳ "+fmtbn(abs(t["profit"])),color=pc,bold=True,align="right",bg=alt(i),size=11)}</tr>\n'
    s3+=f'<tr style="{tot}"><td style="padding:6px 9px;border:1px solid #C8DCF0">মোট</td><td colspan="5" style="padding:6px 9px;border:1px solid #C8DCF0"></td><td style="padding:6px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["blue"]}">৳ {fmtbn(tBill)}</td><td style="padding:6px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["teal"]}">৳ {fmtbn(tFare)}</td><td style="padding:6px 9px;border:1px solid #C8DCF0;text-align:right;color:{C["gold"]}">৳ {fmtbn(tVAT+tCOF)}</td><td style="padding:6px 9px;border:1px solid #C8DCF0;text-align:right;color:{tc}">{tsg}৳ {fmtbn(abs(tProfit))}</td></tr>'

    return f"""<!DOCTYPE html><html lang="bn"><head><meta charset="UTF-8">
<style>
  @page {{ size:A4; margin:13mm; }}
  *{{ box-sizing:border-box; margin:0; padding:0; }}
  body{{ font-family:'Noto Sans Bengali','Hind Siliguri',sans-serif; color:{C['navy']}; font-size:13px;
        -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  h2{{ font-size:15px; font-weight:700; color:{C['navy']}; margin:14px 0 6px;
      padding-bottom:4px; border-bottom:3px solid {C['sky']}; }}
  table{{ width:100%; border-collapse:collapse; margin-bottom:2px; }}
  .footer{{ margin-top:18px; padding-top:7px; border-top:1px solid #D0DEF0;
            display:flex; justify-content:space-between; }}
</style>
</head><body>

<div style="display:flex;justify-content:space-between;align-items:center;
     padding-bottom:7px;border-bottom:3px solid {C['sky']};margin-bottom:9px">
  <div style="font-size:20px;font-weight:700">{company}</div>
  <div style="font-size:11px;color:#7A9ABF;font-family:monospace">পরিবহন বিল লগ</div>
</div>

<div style="text-align:center;font-size:19px;font-weight:700;margin-bottom:4px">পরিবহন বিল লগ — প্রতিবেদন</div>
<div style="text-align:center;font-size:12px;color:{C['muted']};margin-bottom:3px">
  মোট যাত্রা: {bn(len(trips))}টি &nbsp;|&nbsp; মোট বিল: ৳{fmtbn(tBill)} &nbsp;|&nbsp;
  নেট লাভ: <span style="color:{tc};font-weight:700">{tsg}৳{fmtbn(abs(tProfit))}</span>
</div>
<div style="text-align:center;font-size:11px;color:#9EAFC0;margin-bottom:14px;
     padding-bottom:6px;border-bottom:1px solid #E0EAFA">
  রিপোর্ট তৈরির সময়ঃ &nbsp;{now_bst()}&nbsp; (স্বয়ংক্রিয়ভাবে তৈরি)
</div>

<h2>১.&nbsp; মোট আর্থিক সারসংক্ষেপ</h2>
<table><thead><tr>{th('ক্র.','center','40px')}{th('বিবরণ','left')}{th('পরিমাণ (টাকা)','right','150px')}{th('মন্তব্য','left','160px')}</tr></thead>
<tbody>{s1}</tbody></table>

<h2>২.&nbsp; দৈনিকভিত্তিক বিবরণ</h2>
<table><thead><tr>{th('তারিখ')}{th('যাত্রা','center','50px')}{th('মোট বিল (৳)','right')}{th('মোট ভাড়া (৳)','right')}{th('ভ্যাট+COF (৳)','right')}{th('নেট লাভ (৳)','right')}</tr></thead>
<tbody>{s2}</tbody></table>

<h2>৩.&nbsp; সম্পূর্ণ যাত্রা তালিকা</h2>
<table><thead><tr>{th('ক্র.','center','28px')}{th('তারিখ','center','65px')}{th('ট্রাক','center','65px')}{th('ডিলার','left')}{th('গন্তব্য','center','75px')}{th('বর্গফুট','right','58px')}{th('বিল','right','68px')}{th('ভাড়া','right','65px')}{th('ভ্যাট-COF','right','70px')}{th('লাভ (৳)','right','75px')}</tr></thead>
<tbody>{s3}</tbody></table>

<div class="footer">
  <div style="font-size:12px;color:{C['muted']}">তথ্য প্রদানকারীঃ &nbsp;<strong style="color:{C['navy']}">{provider}</strong></div>
  <div style="font-size:10px;color:#C8D8EA;font-family:monospace">XLedger v2.0 | by Mishu</div>
</div>
</body></html>"""

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
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            f.write(html_content); html_path = f.name
        pdf_path = html_path.replace('.html', '.pdf')
        subprocess.run([
            'wkhtmltopdf',
            '--page-size','A4','--margin-top','13mm','--margin-bottom','13mm',
            '--margin-left','13mm','--margin-right','13mm',
            '--encoding','UTF-8','--enable-local-file-access','--quiet',
            html_path, pdf_path
        ], timeout=30)
        os.unlink(html_path)
        with open(pdf_path, 'rb') as f: pdf_bytes = f.read()
        os.unlink(pdf_path)
        from datetime import date
        filename = f"XLedger_Report_{date.today().strftime('%d-%m-%Y')}.pdf"
        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        return f'ত্রুটি: {str(e)}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

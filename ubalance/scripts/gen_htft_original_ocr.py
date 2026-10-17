# -*- coding: utf-8 -*-
"""
Faithful OCR transcription of the ORIGINAL Loan Agreement HT/FT 012025
(Huatex Vietnam -> Viet Nam Future Textile), scanned 2025-12-04.
No content changes: original drafting inconsistencies are preserved as printed.
"""
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

OUT = "/Users/zhaoyuzhao/.openclaw/workspace-balance/output"
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "Hop_dong_vay_HT-FT_012025_Ban_goc_OCR_EN-VI.docx")

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(3)
st.paragraph_format.line_spacing = 1.15

for s in doc.sections:
    s.top_margin = Cm(2.2)
    s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.5)
    s.right_margin = Cm(2.0)


def P(text="", bold=False, italic=False, align=None, size=11, sb=0, sa=3, indent=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    r.font.name = "Times New Roman"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    return p


def EN(text, **kw):
    kw.setdefault("sb", 6)
    return P(text, **kw)


def VI(text, **kw):
    kw.setdefault("sb", 0)
    kw.setdefault("sa", 6)
    return P(text, italic=True, **kw)


J = WD_ALIGN_PARAGRAPH.JUSTIFY

# ------------------------------------------------------------------ PAGE 1
P("LOAN AGREEMENT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, sa=0)
P("HỢP ĐỒNG VAY", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, sa=8)

P("No./Số: HT/FT 012025", bold=True, sa=8)

P("2025 January 2nd                Dong Nai, Vietnam", sa=0)
VI("Ngày 02 tháng 10 năm 2025                Đồng Nai, Việt Nam", sa=10)

EN("THIS AGREEMENT is entered into as of the date hereunder between:", align=J)
VI("Hợp đồng này được ký kết vào ngày dưới đây, giữa:", align=J)

EN("1. HUATEX VIETNAM COMPANY LIMITED, a company duly incorporated and operating under the "
   "laws of Vietnam whose Enterprise registration certificate No. 3603695597, address: No. 6 "
   "Street, Nhon Trach VI Industrial Park, Phuoc An Commune, Dong Nai, Vietnam, represented "
   "by: Mr. CHEN, HUI, (hereinafter referred as \u201cLender\u201d), and", align=J)
VI("1. HUATEX VIETNAM COMPANY LIMITED, một công ty được thành lập và hoạt động theo luật pháp "
   "của Việt Nam với Giấy chứng nhận đăng ký doanh nghiệp số 3603695597, địa chỉ: Đường số 6, "
   "KCN Nhơn Trạch VI, Xã Phước An, Đồng Nai, Việt Nam, được đại diện bởi ông CHEN, HUI (sau "
   "đây gọi là \u201cBên cho vay\u201d), và", align=J)

EN("2. VIET NAM FUTURE TEXTILE COMPANY LIMITED, a legal entity registered and operating in "
   "accordance with the laws of Viet Nam whose Enterprise registration certificate No. "
   "3901352789, address: Lot B11.3, Street C4, Thanh Thanh Cong Industrial Park, Trang Bang "
   "Ward, Tay Ninh Province, Viet Nam, duly represented by Mr. HUANG CHAOGUI (hereinafter "
   "referred as the \u201cBorrower\u201d).", align=J)
VI("2. VIET NAM FUTURE TEXTILE COMPANY LIMITED, là một pháp nhân được đăng ký và hoạt động theo "
   "quy định của pháp luật của Việt Nam; Giấy chứng nhận đăng ký doanh nghiệp số 3901352789, "
   "địa chỉ: Lô B11.3, đường C4, Khu công nghiệp Thành Thành Công, Phường Trảng Bàng, Tỉnh Tây "
   "Ninh, Việt Nam, được đại diện hợp pháp bởi ông HUANG CHAOGUI (sau đây gọi là \u201cBên "
   "vay\u201d).", align=J)

EN("(each referred to as \u201cParty,\u201d and jointly the \u201cParties\u201d).", align=J)
VI("(mỗi bên sau đây gọi là \u201cBên\u201d và cùng nhau gọi là \u201cCác Bên\u201d).", align=J)

EN("A. WHEREAS, the Lender has agreed to lend to the Borrower the Loan (as defined below) on "
   "the terms and conditions as set forth herein; and", align=J)
VI("A. Xét rằng, Bên cho vay đồng ý cấp một khoản vay cho Bên vay (như được định nghĩa dưới "
   "đây) theo các điều khoản và điều kiện quy định trong thỏa thuận này; và", align=J)

EN("B. WHEREAS, the Borrower will use the Loan for all operations of the Company in compliance "
   "with legal regulations and has agreed to pay interest on the Loan, as described below.", align=J)
VI("B. Xét rằng, Bên vay sẽ sử dụng khoản vay này cho toàn bộ hoạt động của Công ty đảm bảo "
   "đúng quy định pháp luật và đã đồng ý trả lãi suất cho khoản vay, như được mô tả dưới đây.", align=J)

EN("NOW, THEREFORE, it is agreed as follows:", bold=True, align=J)
VI("Vì vậy, các bên đồng ý như sau:", bold=True, align=J)

# ------------------------------------------------------------------ PAGE 2
P("1. The Loan", bold=True, sb=12, sa=0)
P("1. Khoản vay", bold=True, italic=True, sa=6)

EN("1.1. Subject to the terms and conditions set forth herein, the Lender shall lend to "
   "Borrower the aggregate original principal amount of up to One hundred and thirty-two "
   "billion Vietnamese Dong (132.000.000.000 VND) (hereinafter the \u201cLoan\u201d).", align=J)
VI("1.1. Theo các điều khoản và điều kiện được quy định trong đây, Bên cho vay sẽ cho Bên vay "
   "vay tổng số tiền gốc lên đến Một trăm ba mươi hai tỷ đồng (132.000.000.000 VND) (sau đây "
   "gọi là \u201cKhoản Vay\u201d).", align=J)

EN("1.2. The purpose of the Loan is the replenishment for all operations of the Company in "
   "compliance with legal regulations.", align=J)
VI("1.2. Mục đích của Khoản Vay là để cho toàn bộ hoạt động của Công ty đảm bảo đúng quy định "
   "pháp luật.", align=J)

P("2. Drawdown", bold=True, sb=10, sa=0)
P("2. Giải ngân", bold=True, italic=True, sa=6)

EN("2.1. The Loan shall be drawn down in one or more installments (each installment the "
   "\u201cDrawdown\u201d).", align=J)
VI("2.1. Khoản Vay sẽ được giải ngân thành một hoặc nhiều đợt (mỗi đợt gọi là \u201cLần Giải "
   "Ngân\u201d).", align=J)

EN("2.2. The Parties agree that the Drawdown shall be considered disbursed in full in case of "
   "transfer to the Borrower of funds in amount of the respective Drawdown from the Lender's "
   "bank account to the Borrower's Account. The Drawdown Date shall mean the date of 1st "
   "installment credited to Borrower's bank account.", align=J)
VI("2.2. Các Bên đồng ý rằng Lần Giải Ngân sẽ được coi là đã được thực hiện đầy đủ khi số tiền "
   "tương ứng của Lần Giải Ngân được chuyển từ tài khoản ngân hàng của Bên cho vay sang tài "
   "khoản của Bên vay. Ngày Giải Ngân sẽ có nghĩa là ngày của đợt giải ngân đầu tiên được ghi "
   "có vào tài khoản ngân hàng của Bên vay.", align=J)

P("3. Repayment", bold=True, sb=10, sa=0)
P("3. Hoàn trả", bold=True, italic=True, sa=6)

EN("3.1. The Borrower shall repay each Drawdown on the respective Repayment Date (as defined "
   "below).", align=J)
VI("3.1. Bên vay sẽ hoàn trả cho mỗi lần Giải ngân vào Ngày hoàn trả tương ứng (được quy định "
   "dưới đây).", align=J)

EN("3.2. Repayment Date for each respective Drawdown means the date, which:", align=J)
VI("3.2. Ngày hoàn trả cho mỗi lần giải ngân tương ứng được xác định là:", align=J)

EN("a) Up to 360 days from the date of receiving the loan, the company has the right to repay "
   "the loan early;", align=J, indent=0.6)
VI("a) Tối đa 360 ngày kể từ ngày nhận được tiền vay, công ty được quyền trả nợ trước hạn;",
   align=J, indent=0.6)

EN("b) in case, when the Repayment Date, on which the respective Drawdown repayment must be "
   "performed, falls on a non-business day in Vietnam, the Repayment Date shall be the next "
   "following business day.", align=J, indent=0.6)
VI("b) trường hợp Ngày hoàn trả của khoản vay tương ứng rơi vào ngày không làm việc ở Việt Nam, "
   "thì Ngày hoàn trả sẽ là ngày làm việc kế tiếp.", align=J, indent=0.6)

# ------------------------------------------------------------------ PAGE 3
EN("3.3. Each Drawdown shall be repaid on the respective Repayment Date by wire transfer "
   "according to the payment details of the Lender, as specified in section 7 (the "
   "\u201cLender's Account\u201d).", align=J, sb=8)
VI("3.3. Mỗi khoản vay sẽ được hoàn trả vào Ngày hoàn trả tương ứng bằng cách chuyển tiền theo "
   "thông tin tài khoản của Bên Cho Vay được ghi trong mục 7.", align=J)

P("4. Interest", bold=True, sb=10, sa=0)
P("4. Lãi suất", bold=True, italic=True, sa=6)

EN("4.1. Interest shall be calculated and accrue on the basis of the actual number of days "
   "elapsed and a 365-day year on the outstanding total amount of all Drawdowns disbursed "
   "within the Loan starting from the respective Drawdown Date of each Drawdown.", align=J)
VI("4.1. Lãi suất sẽ được tính và tích lũy dựa trên số ngày thực tế đã trôi qua và năm 365 "
   "ngày, trên tổng số tiền còn nợ của tất cả các khoản vay đã giải ngân trong khoản vay, tính "
   "từ Ngày Giải Ngân của từng khoản vay.", align=J)

EN("4.2. The interest on all Drawdowns disbursed within the Loan shall be due and payable on "
   "the Repayment Date of the last outstanding Drawdown.", align=J)
VI("4.2. Lãi suất đối với tất cả các khoản vay đã giải ngân trong khoản vay sẽ đến hạn và phải "
   "được thanh toán vào Ngày hoàn trả của khoản vay còn lại cuối cùng.", align=J)

EN("4.3. The interest rate for each Drawdown equals to 4% per annum.", align=J)
VI("4.3. Lãi suất đối với mỗi khoản vay là 4%/năm.", align=J)

P("5. Miscellaneous", bold=True, sb=10, sa=0)
P("5. Các điều khoản khác", bold=True, italic=True, sa=6)

EN("5.1. Any changes and/or amendments to the Agreement shall be made by the Parties through "
   "execution of an additional agreement to be signed by authorized persons.", align=J)
VI("5.1. Mọi thay đổi và/hoặc sửa đổi đối với Hợp đồng phải được thực hiện bởi các Bên thông "
   "qua việc ký kết một hợp đồng bổ sung, do các đại diện có thẩm quyền ký.", align=J)

EN("5.2. All payments to be made by the Borrower shall be made to the Lender in immediately "
   "available and freely transferable funds for full value on the due date to such account as "
   "the Lender may specify.", align=J)
VI("5.2. Tất cả các khoản thanh toán của Bên vay phải được thực hiện cho Bên cho vay bằng tiền "
   "ngay lập tức có thể sử dụng và chuyển nhượng tự do với đầy đủ giá trị vào ngày đến hạn đến "
   "tài khoản mà Bên cho vay chỉ định.", align=J)

EN("5.3. Payment of all expenses, related to the Loan, including correspondent banks fees and "
   "commissions, shall be carried by the beneficiary of the payment.", align=J)
VI("5.3. Việc thanh toán tất cả các chi phí liên quan đến khoản vay, bao gồm phí và hoa hồng "
   "của các ngân hàng đại lý, sẽ do bên nhận tiền thanh toán chịu.", align=J)

EN("5.4. Each of the Lender and the Borrower shall bear and pay its own costs in connection "
   "with the preparation and execution of this Agreement. Each Party shall pay its own stamp, "
   "documentary, registration or other like duties or taxes imposed on or in connection with "
   "this Agreement or the Loan and shall indemnify the other Party against any liability arising "
   "by reason of any delay or omission to pay such duties or taxes.", align=J)
VI("5.4. Mỗi Bên cho vay và Bên vay sẽ chịu và thanh toán các chi phí của mình liên quan đến "
   "việc chuẩn bị và ký kết Hợp đồng này. Mỗi Bên sẽ tự thanh toán các lệ phí, thuế tem, thuế "
   "tài liệu, thuế đăng ký hoặc các loại thuế tương tự khác liên quan đến Hợp đồng hoặc khoản "
   "vay và sẽ bồi thường cho Bên kia về bất kỳ nghĩa vụ nào phát sinh do việc chậm trễ hoặc "
   "thiếu sót trong việc thanh toán các lệ phí hoặc thuế đó.", align=J)

# ------------------------------------------------------------------ PAGE 4
EN("5.5. No failure or delay on the part of the Lender to exercise any power, right or remedy "
   "under this Agreement shall operate as a waiver of such power, right or remedy, nor shall "
   "any single or partial exercise by the Lender of any power, right or remedy preclude any "
   "other or further exercise thereof or the exercise of any other power, right or remedy.", align=J, sb=8)
VI("5.5. Việc Bên cho vay không thực hiện hoặc chậm thực hiện bất kỳ quyền lực, quyền hoặc "
   "biện pháp khắc phục nào theo Hợp đồng này sẽ không được coi là từ bỏ quyền lực, quyền hoặc "
   "biện pháp khắc phục đó, và việc Bên cho vay chỉ thực hiện một phần hoặc một lần quyền lực, "
   "quyền hoặc biện pháp khắc phục sẽ không ngăn cản việc thực hiện bất kỳ quyền lực, quyền "
   "hoặc biện pháp khắc phục khác hoặc thêm vào.", align=J)

EN("5.6. The Agreement takes effect upon its signing by both Parties and remains valid until "
   "full performance by the Parties of their respective obligations hereunder.", align=J)
VI("5.6. Hợp đồng có hiệu lực ngay khi được cả hai Bên ký và vẫn còn hiệu lực cho đến khi các "
   "Bên hoàn thành đầy đủ các nghĩa vụ của mình theo Hợp đồng này.", align=J)

P("6. Governing Law and Jurisdiction", bold=True, sb=10, sa=0)
P("6. Luật áp dụng và quyền tài phán", bold=True, italic=True, sa=6)

EN("6.1. This Agreement shall be governed by and construed in accordance with Chinese law.", align=J)
VI("6.1. Hợp đồng này sẽ được điều chỉnh và giải thích theo pháp luật của Trung Quốc.", align=J)

EN("6.2. Any dispute arising out of or in connection with this Agreement (including a dispute "
   "regarding the existence, validity or termination of this Agreement) shall be referred to "
   "and finally resolved by Chinese Courts.", align=J)
VI("6.2. Mọi tranh chấp phát sinh từ hoặc liên quan đến Hợp đồng này (bao gồm tranh chấp liên "
   "quan đến sự tồn tại, hiệu lực hoặc chấm dứt của Hợp đồng này) sẽ được đưa ra và giải quyết "
   "cuối cùng bởi các Tòa án của Trung Quốc.", align=J)

P("7. Payment details", bold=True, sb=10, sa=0)
P("7. Thông tin thanh toán", bold=True, italic=True, sa=6)

EN("Payments under this Agreement are held to and from such Parties banking details:", align=J)
VI("Các khoản thanh toán theo Hợp đồng này sẽ được thực hiện đến và từ thông tin tài khoản "
   "ngân hàng của các Bên như sau:", align=J)

P("The Borrower: VIET NAM FUTURE TEXTILE COMPANY LIMITED", bold=True, sb=8, sa=0)
VI("Bên vay: VIET NAM FUTURE TEXTILE COMPANY LIMITED", bold=True, sa=2)

P("Legal Address: Lot B11.3, Street C4, Thanh Thanh Cong Industrial Park, Trang Bang Ward, "
  "Tay Ninh Province, Viet Nam.", size=10.5, align=J, sb=2, sa=1)
VI("Địa chỉ hợp pháp: Lô B11.3, đường C4, KCN Thành Thành Công, Phường Trảng Bàng, Tỉnh Tây "
   "Ninh, Việt Nam.", size=10.5, align=J, sa=2)
P("Account No.: \u2026\u2026\u2026\u2026\u2026\u2026\u2026 (USD)", size=10.5, sa=1)
P("Account No.:", size=10.5, sa=1)
P("- 1863636868 (VND) - MB Bank - Tam Hiep Branch", size=10.5, sa=1)
P("- 111002998317 (VND) - Vietinbank - Nhon Trach Branch", size=10.5, sa=2)
P("Bank Name: Military Commercial Joint Stock Bank - Tam Hiep Branch; Vietnam Joint Stock "
  "Commercial Bank for Industry and Trade - Nhon Trach Branch.", size=10.5, align=J, sa=1)
P("Bank's address: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026 Vietnam", size=10.5, sa=2)

VI("Số tài khoản: \u2026\u2026\u2026\u2026\u2026\u2026\u2026 (USD)", size=10.5, sa=1)
VI("Số tài khoản:", size=10.5, sa=1)
VI("- 1863636868 (VND) - MB Bank - CN Tam Hiệp", size=10.5, sa=1)
VI("- 111002998317 (VND) - Vietinbank - CN Nhơn Trạch", size=10.5, sa=2)
VI("Tên ngân hàng: Ngân hàng Thương mại Cổ phần Quân đội - Chi nhánh Tam Hiệp; Ngân hàng "
   "Thương mại Cổ phần Công Thương Việt Nam - Chi nhánh Nhơn Trạch.", size=10.5, align=J, sa=1)
VI("Địa chỉ ngân hàng: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026", size=10.5, sa=1)
VI("Mã SWIFT của Ngân hàng: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026", size=10.5, sa=2)

# ------------------------------------------------------------------ PAGE 5
P("The Lender: HUATEX VIETNAM COMPANY LIMITED", bold=True, sb=10, sa=0)
VI("Bên cho vay: CÔNG TY TNHH HUATEX VIỆT NAM", bold=True, sa=2)

P("Legal Address: No. 6 Street, Nhon Trach VI Industrial Park, Phuoc An Commune, Dong Nai, "
  "Vietnam", size=10.5, align=J, sb=2, sa=1)
VI("Địa chỉ hợp pháp: Đường số 6, Khu công nghiệp Nhơn Trạch, Xã Long Thọ, huyện Nhơn Trạch, "
   "tỉnh Đồng Nai", size=10.5, align=J, sa=2)
P("Account No.: \u2026\u2026\u2026\u2026\u2026\u2026\u2026 (USD)", size=10.5, sa=1)
P("Account No.:", size=10.5, sa=1)
P("- 111002923670 (VND) - Vietinbank", size=10.5, sa=1)
P("- 5656568568 (VND) - MB", size=10.5, sa=2)
P("Bank Name: Military Commercial Joint Stock Bank - Tam Hiep Branch; Vietnam Joint Stock "
  "Commercial Bank for Industry and Trade - Nhon Trach Branch", size=10.5, align=J, sa=1)
P("Bank's address: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026 Vietnam", size=10.5, sa=2)

VI("Số tài khoản: \u2026\u2026\u2026\u2026\u2026\u2026\u2026 (USD)", size=10.5, sa=1)
VI("Số tài khoản: \u2026\u2026\u2026\u2026\u2026\u2026\u2026 (VND)", size=10.5, sa=1)
VI("- 111002923670 (VND) - Vietinbank", size=10.5, sa=1)
VI("- 5656568568 (VND) - MB", size=10.5, sa=2)
VI("Tên ngân hàng: Ngân hàng Thương mại Cổ phần Quân đội - Chi nhánh Tam Hiệp; Ngân hàng "
   "Thương mại Cổ phần Công Thương Việt Nam - Chi nhánh Nhơn Trạch.", size=10.5, align=J, sa=1)
VI("Địa chỉ ngân hàng: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026", size=10.5, sa=1)
VI("Mã SWIFT của Ngân hàng: \u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026\u2026", size=10.5, sa=2)

# ------------------------------------------------------------------ PAGE 6
P("8. General terms", bold=True, sb=10, sa=0)
P("8. Điều khoản chung", bold=True, italic=True, sa=6)

EN("8.1. This Agreement is made in 02 original copies. Each party keeps 01 copy with equal "
   "legality for implementation.", align=J)
VI("8.1. Hợp đồng này được lập thành 02 bản. Mỗi bên giữ một bản có giá trị pháp lý như nhau "
   "để thực hiện.", align=J)

EN("8.2. In witness whereof, the Parties hereto have signed this Agreement on the date "
   "mentioned earlier.", align=J)
VI("8.2. Để ghi nhận sự thỏa thuận, các Bên tham gia dưới đây đã tiến hành ký kết Hợp đồng này "
   "vào ngày được đề cập đầu tiên ở trên.", align=J)

P("", sa=12)
sig = doc.add_table(rows=1, cols=2)
sig.alignment = WD_TABLE_ALIGNMENT.CENTER
L, R = sig.rows[0].cells

def sigcell(cell, lines):
    cell.paragraphs[0].text = ""
    first = True
    for txt, bold, italic in lines:
        p = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(txt)
        r.bold, r.italic = bold, italic
        r.font.size = Pt(10.5)
        r.font.name = "Times New Roman"

sigcell(L, [
    ("For and on behalf of", False, False),
    ("Thay mặt và đại diện cho", False, True),
    ("The Borrower/ Bên Vay", False, False),
    ("", False, False),
    ("VIET NAM FUTURE TEXTILE", True, False),
    ("COMPANY LIMITED", True, False),
    ("", False, False),
    ("", False, False),
    ("", False, False),
    ("HUANG CHAOGUI", True, False),
])
sigcell(R, [
    ("For and on behalf of", False, False),
    ("Thay mặt và đại diện cho", False, True),
    ("The Lender/ Bên cho vay", False, False),
    ("", False, False),
    ("HUATEX VIETNAM", True, False),
    ("COMPANY LIMITED", True, False),
    ("", False, False),
    ("", False, False),
    ("", False, False),
    ("CHEN HUI", True, False),
])

doc.save(PATH)
print("SAVED:", PATH)

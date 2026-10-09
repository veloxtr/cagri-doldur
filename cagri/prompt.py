# -*- coding: utf-8 -*-
"""Form alanları, AI kuralları ve örnek çağrılar."""
import json

# Alanlar, çağrı ekranındaki yukarıdan aşağı sırayla
FIELDS = [
    ("cozum", "Uygulanan çözüm"),
    ("sonuc", "Sonuç / doğrulama"),
    ("ozet", "Sorunun özeti"),
    ("kontroller", "Yapılan kontroller"),
    ("kok_neden", "Kök neden / tespit edilemedi"),
    ("sonraki", "Sonraki adım / sorumlu / dönüş zamanı"),
    ("ucret", "Ücret bilgisi veya ücretsiz işlem gerekçesi"),
    ("kayit", "Kayıt numarası müşteriye bildirildi"),
]


# Bugün birlikte doldurduğumuz örnekler: AI bu tarzı taklit eder.
ORNEKLER = [
    (
        "müşteri eski tarihli bir setup kullanıyordu sürekli demoya düşme sorunu güncel setup ile güncelleme yapıldı sorun düzeldi . müşterinin sözleşmesi olduğu için ücret talep edilmedi",
        {
            "cozum": "Güncel setup ile programın güncellemesi yapıldı.",
            "sonuc": "Güncelleme sonrası program kontrol edildi, demo moduna düşme sorunu giderildi.",
            "ozet": "Müşteri, eski tarihli bir kurulum (setup) dosyası kullandığı için program sürekli demo moduna düşüyordu.",
            "kontroller": "Müşterinin kullandığı setup sürümü kontrol edildi; güncel sürüm olmadığı ve eski tarihli olduğu görüldü.",
            "kok_neden": "Kök neden tespit edildi: güncel olmayan, eski tarihli setup kullanılması.",
            "sonraki": "Ek bir işlem gerekmiyor. Sorun tekrarlarsa müşteri destek hattına tekrar ulaşabilir; kayıt kapatılabilir.",
            "ucret": "Ücret talep edilmedi; müşterinin geçerli bakım/destek sözleşmesi bulunduğu için işlem sözleşme kapsamında ücretsiz yapıldı.",
            "kayit": "Hayır",
        },
    ),
    (
        "efatura ve eirsaliye lisdansı yeni crm de yoktu ikisinin de daha çönceden satışı olduğu için satış ekibiyle göüştüm lisanslarını girdiler müşteriye tekrardan lisanslama yapıldı ve sorun çözüldü",
        {
            "cozum": "Satış ekibi ile görüşüldü, lisanslar yeni CRM'e tanımlandı. Ardından müşterinin lisanslaması yeniden yapıldı.",
            "sonuc": "Yeniden lisanslama sonrası e-Fatura ve e-İrsaliye modüllerinin aktif olduğu kontrol edildi, sorun çözüldü.",
            "ozet": "Müşterinin e-Fatura ve e-İrsaliye lisansları yeni CRM sisteminde görünmüyordu.",
            "kontroller": "Yeni CRM'de lisans kayıtları kontrol edildi, e-Fatura ve e-İrsaliye lisanslarının tanımlı olmadığı görüldü. Satış geçmişi incelendi, her iki ürünün de daha önce müşteriye satıldığı doğrulandı.",
            "kok_neden": "Kök neden tespit edildi: daha önce satışı yapılmış e-Fatura ve e-İrsaliye lisansları yeni CRM'e aktarılmamıştı.",
            "sonraki": "Ek bir işlem gerekmiyor, kayıt kapatılabilir.",
            "ucret": "Ücret talep edilmedi. Lisanslar daha önce satın alınmış, sorun yeni CRM'e aktarım eksikliğinden kaynaklandığı için işlem ücretsiz yapıldı.",
            "kayit": "Hayır",
        },
    ),
    (
        "portalde şifre güncellenmiş bilnexe de eklemek gerekiyordu bilnexe de yueni şifreler eklendi sorun çözüldü müşterinin çözüldüğüne dair onayı alındı",
        {
            "cozum": "Yeni şifreler Bilnex'e tanımlandı.",
            "sonuc": "Şifre güncellemesi sonrası bağlantının çalıştığı kontrol edildi, sorun çözüldü. Müşteriden sorunun çözüldüğüne dair onay alındı.",
            "ozet": "Müşterinin portal şifresi güncellenmiş, ancak yeni şifre Bilnex'e tanımlanmadığı için bağlantı sorunu yaşanıyordu.",
            "kontroller": "Bilnex'teki portal bağlantı bilgileri kontrol edildi, kayıtlı şifrenin portaldeki güncel şifreyle uyuşmadığı görüldü.",
            "kok_neden": "Kök neden tespit edildi: portalde şifre değiştirilmiş, ancak yeni şifre Bilnex'e girilmemişti.",
            "sonraki": "Ek bir işlem gerekmiyor, kayıt kapatılabilir. Müşteriye, portalde ileride şifre değişikliği yaparsa Bilnex'te de güncellemesi gerektiği hatırlatıldı.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
    (
        "eski mobilnex(el terminali kullanıyor) eski mobilnex den bir satış faturası oluşmuş bilnexe aktarılmış ama evrağın içi boş du . kablolu bir şekilde bilgisayara bağlamasını istedik kablopsu yokmuş o yüzden bağlanıp kontrol edemedik. kablo bbulup bağlayacak ona göre bakacağız kendisai sönüş sağlayacak . mobilnex yıllık yenilemeli olduğu için ücretsiz işlem yaptık ve müşterimnin sözleşmesi var",
        {
            "cozum": "Henüz çözüm uygulanmadı. Müşteriden kablo temin ederek el terminalini bilgisayara bağlaması istendi.",
            "sonuc": "Sorun devam ediyor. Kontrol, cihaz bilgisayara bağlandıktan sonra yapılacak.",
            "ozet": "Müşterinin el terminalinde kullandığı eski Mobilnex'ten oluşturulan bir satış faturası Bilnex'e aktarılmış, ancak evrakın içi boş geliyordu.",
            "kontroller": "Bilnex'e aktarılan satış faturası incelendi, evrak içeriğinin boş olduğu görüldü. El terminalinin kontrol edilmesi için cihazın kablo ile bilgisayara bağlanması istendi, ancak müşteride kablo olmadığı için bağlantı kurulamadı.",
            "kok_neden": "Kök neden tespit edilemedi. El terminaline bağlanılamadığı için evrakın neden boş aktarıldığı henüz belirlenemedi.",
            "sonraki": "Müşteri kablo temin edip el terminalini bilgisayara bağladığında dönüş sağlayacak. Dönüş sonrası cihaz ve aktarım tarafı destek ekibi tarafından incelenecek.",
            "ucret": "Ücret talep edilmedi. Mobilnex yıllık yenilemeli bir ürün olduğu ve müşterinin geçerli sözleşmesi bulunduğu için işlem ücretsiz yapıldı.",
            "kayit": "Hayır",
        },
    ),
    (
        "bilnex den efatura göndermeye çalışıyor entegratör edm. normalde bu sorun edm nin seri numarası kısmında son fatura no yu güncellememesinin kaynaklanıyor idi. manuel olarak edm tanımlar son seri no kısmındda son fgönderilen faturanın fatura numarasını verince düzeliyordu ama edm ye herhangi bir şekilde müdahale etmeden deneme amaçlı gönderim sağladığımda dfatura direkt gönderildi edm den de kontrol ettim fatura seri no larında son aldığı numaralar da doğru.herhangi bir sorun yok done olmadığı için test edemedik ama faturası gönderildi herhangi bir sorun yok anlık oluşan durum ghgibi.",
        {
            "cozum": "Herhangi bir müdahale gerekmedi. Bilnex üzerinden deneme gönderimi yapıldı ve fatura başarıyla iletildi.",
            "sonuc": "Bilnex'ten fatura gönderimi sorunsuz gerçekleşti, EDM seri numaraları doğru. Hata tekrar oluşmadığı için sorun durumu test edilemedi, ancak şu an için bir problem görünmüyor.",
            "ozet": "Müşteri Bilnex üzerinden e-Fatura göndermeye çalışırken sorun yaşadığını bildirdi (entegratör: EDM).",
            "kontroller": "EDM tanımlarında fatura seri numaraları kontrol edildi, son alınan numaraların doğru olduğu görüldü. EDM'ye müdahale edilmeden Bilnex üzerinden deneme amaçlı fatura gönderimi yapıldı ve EDM portalından gönderimin başarılı olduğu doğrulandı.",
            "kok_neden": "Kök neden tespit edilemedi. Kontrol sırasında hata tekrarlanmadı; anlık oluşan bir durum olduğu düşünülüyor. Benzer vakalarda neden, EDM'de son seri numarasının güncellenmemesiydi; ancak bu vakada seri numaraları doğru görüldü.",
            "sonraki": "Sorun tekrarlarsa müşteri dönüş sağlayacak. Tekrarlaması halinde EDM tanımlarında son seri numarası alanına son gönderilen faturanın numarası manuel olarak girilerek çözülebilir.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
    (
        "bayiden geldi-B2b den gelen siparişlerde fatura aktarımında rapor kontrol ediyor(fatura karlılık).raporda oluşturan kullanıcı web olarak görüşüyor orda değişiklik istiyor ne gibi bir değişiklik istediği tam anlaşılamadı .kendi tarafımda kontrol sağladım ama müdahele edilecek bir kısım yok gibi.müşteri yetkilisi müsait değilmiş tam olarak istişare ed3emedik.müsait olduğunda kendisi dönüş sağlayacak ona göre i,nceleyip istişare edeceğiz",
        {
            "cozum": "Henüz bir çözüm uygulanmadı. Talebin netleştirilmesi için müşteri yetkilisi ile görüşülmek istendi, ancak kendisi müsait olmadığı için istişare yapılamadı.",
            "sonuc": "Konu açık. Müşteri talebi netleşmeden işlem yapılamıyor.",
            "ozet": "Kayıt bayi üzerinden iletildi. Müşteri, B2B'den gelen siparişlerin faturaya aktarımında Fatura Karlılık raporunu kontrol ediyor; raporda 'Oluşturan Kullanıcı' alanı 'Web' olarak görünüyor ve bu alanda değişiklik istiyor. Ancak tam olarak nasıl bir değişiklik istendiği netleşmedi.",
            "kontroller": "Fatura Karlılık raporu ve B2B siparişlerinden aktarılan faturalar kontrol edildi. 'Oluşturan Kullanıcı' alanında müdahale edilecek bir durum görülmedi.",
            "kok_neden": "Kök neden tespit edilemedi. Müşterinin talebi tam olarak anlaşılamadığı için konu netleştirilemedi.",
            "sonraki": "Müşteri yetkilisi müsait olduğunda dönüş sağlayacak. Dönüşü sonrası talep netleştirilip incelenecek ve istişare edilerek gerekli işlem yapılacak.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
    (
        "türmob key alma konusunda destek ister . bizim tarafımızdan alınmadığını mali müşavirin kendi portali üzerinden giriş yapıp alması gerektiğini söyledim.mali müşvari nasıl alınacağını bilmiyormuş.bişzim o tarafa müdahale edemeyeceğimizi.yetkimiz olmadığını mali müşvcarilerin alabildiği bir key olduğunu söyledim",
        {
            "cozum": "Müşteriye TÜRMOB key'in mali müşavir tarafından, kendi portalına giriş yapılarak alınması gerektiği bilgisi verildi. Bu tarafa müdahale yetkimiz olmadığı, key'in yalnızca mali müşavirler tarafından alınabildiği açıklandı.",
            "sonuc": "Müşteri bilgilendirildi. İşlem firmamızın yetki alanı dışında olduğu için tarafımızdan yapılacak bir işlem bulunmuyor.",
            "ozet": "Müşteri, TÜRMOB key alma konusunda destek talep etti.",
            "kontroller": "Talep değerlendirildi. TÜRMOB key'in firmamız tarafından alınamadığı, yalnızca mali müşavirin kendi portalı üzerinden alabildiği bir anahtar olduğu teyit edildi.",
            "kok_neden": "Teknik bir sorun bulunmuyor. Talep, firmamızın yetki alanı dışında kalan bir işlemle ilgili.",
            "sonraki": "Key'in alınması mali müşavirin sorumluluğunda. Mali müşavir key'i aldıktan sonra programa tanımlanması gerekirse müşteri dönüş sağlayabilir.",
            "ucret": "Ücret talep edilmedi. Bilgilendirme amaçlı görüşme olduğu için işlem ücretsiz yapıldı.",
            "kayit": "Hayır",
        },
    ),
    (
        "b2b sipariş aktarılmama sorunu vardı servisin güncel olmamasından kaynkalı servise güncellemeyi müsait oldukları bir zamanda yapacağız . siparişleri manuel olarak aktarıldı",
        {
            "cozum": "Bekleyen siparişler geçici çözüm olarak manuel şekilde aktarıldı. Servis güncellemesi henüz yapılmadı.",
            "sonuc": "Bekleyen siparişlerin manuel aktarımı tamamlandı. Kalıcı çözüm için servis güncellemesi bekleniyor.",
            "ozet": "B2B'den gelen siparişler programa aktarılmıyordu.",
            "kontroller": "B2B sipariş aktarım servisi kontrol edildi, servisin güncel sürümde olmadığı görüldü.",
            "kok_neden": "Kök neden tespit edildi: B2B sipariş aktarım servisinin güncel olmaması.",
            "sonraki": "Servis güncellemesi, müşterinin müsait olduğu bir zamanda destek ekibi tarafından yapılacak.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
    (
        "mali müşaviri aradı ebilnex de faturanın red tarihini görmek istiyormuş . ebilnex de red yanıt tarihini göremiyoruz. xml i de aldık gib görünütüleyiciden baktık ama ordqa da red tarihi göstermiyor. karşı taraftan yenıt zarf xml i istemlerini onunla kontrol etmemiz gerektiğini söyledik",
        {
            "cozum": "Mali müşavire, red tarihinin kontrol edilebilmesi için faturayı reddeden karşı taraftan yanıt zarfı XML'ini talep etmesi gerektiği bilgisi verildi.",
            "sonuc": "Mali müşavir bilgilendirildi. Red tarihi, yanıt zarfı XML'i temin edildiğinde kontrol edilebilecek.",
            "ozet": "Müşterinin mali müşaviri, eBilnex'te bir faturanın red tarihini görmek istediğini belirterek destek talep etti.",
            "kontroller": "eBilnex'te faturanın red yanıt tarihinin görüntülenemediği tespit edildi. Faturanın XML dosyası alınarak GİB görüntüleyicide incelendi, burada da red tarihi bilgisinin yer almadığı görüldü.",
            "kok_neden": "Teknik bir sorun bulunmuyor. Red tarihi bilgisi eBilnex'te ve fatura XML'inde yer almıyor; bu bilgi karşı tarafın gönderdiği yanıt zarfı XML'inde bulunuyor.",
            "sonraki": "Mali müşavir, karşı taraftan yanıt zarfı XML'ini temin ettiğinde dönüş sağlayacak; ardından XML üzerinden red tarihi kontrol edilecek.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
    (
        "kontrol sağlandığında fatura kestiği cariilerde vd yazmamış onu yazmasını söyledim. cariilerde hızlıca işlem sağülaması için mali müşavirinden türmob key alması önerildi. key i aldıktaqn sonra bizi arayacak türmob key eklenecek",
        {
            "cozum": "Müşteriye ilgili cari kartlara vergi dairesi bilgisini girmesi gerektiği iletildi. Cari bilgilerinin hızlı doldurulabilmesi için mali müşavirinden TÜRMOB key alması önerildi.",
            "sonuc": "Müşteri bilgilendirildi; vergi dairesi bilgileri girildiğinde sorunun giderilmesi bekleniyor. TÜRMOB key tanımlaması beklemede.",
            "ozet": "Müşteri fatura kesme işleminde sorun yaşadığını bildirdi.",
            "kontroller": "Fatura kesilen cari kartlar kontrol edildi, vergi dairesi bilgisinin girilmediği görüldü.",
            "kok_neden": "Kök neden tespit edildi: fatura kesilen cari kartlarda vergi dairesi bilgisinin eksik olması.",
            "sonraki": "Müşteri, mali müşavirinden TÜRMOB key'i aldıktan sonra dönüş sağlayacak; ardından destek ekibi tarafından key programa tanımlanacak.",
            "ucret": "<VARSAYILAN_UCRET>",
            "kayit": "Hayır",
        },
    ),
]

KURALLAR = """Sen bir yazılım firmasının (Bilnex ERP, eBilnex, Mobilnex, B2B, e-Fatura/e-İrsaliye, EDM entegratörü vb.) teknik destek personeline yardım ediyorsun.
Personel, kapattığı destek çağrısı hakkında kısa, dağınık ve yazım hatalı bir not yazar. Sen bu notu yorumlayıp çağrı kapanış formundaki 8 alana düzgün, resmi Türkçe ile dağıtırsın.

Kurallar:
- Edilgen ve geçmiş zaman kullan ("kontrol edildi", "güncelleme yapıldı", "müşteri bilgilendirildi"). Samimi hitapları ("kanka" vb.) metne alma.
- Nottaki yazım hatalarını düzelt ve dağınık ifadeleri anlamına göre yorumla (ör. "done olmadığı için" = "hata tekrar oluşmadığı için"). Ürün adlarını doğru yaz: Bilnex, eBilnex, Mobilnex, EDM, B2B, TÜRMOB, GİB, CRM, e-Fatura, e-İrsaliye. Kişi adlarını "Ayşe Hanım", "Mehmet Bey" şeklinde yaz.
- Notta olmayan bilgi UYDURMA. Notta açıkça yazmayan ama mantıken çıkan bilgiyi (ör. bir kontrolün yapıldığı) makul ölçüde yazabilirsin.
- Her alan en az bir tam cümle olsun ve nokta ile bitsin ("kayit" alanı hariç).
- "kok_neden": neden belliyse "Kök neden tespit edildi: ..." diye yaz; belli değilse "Kök neden tespit edilemedi." ile başla ve kısa açıkla. Teknik sorun yoksa (bilgi talebi vb.) "Teknik bir sorun bulunmuyor." ile başla.
- "cozum": sorun henüz çözülmediyse bunu açıkça belirt ("Henüz çözüm uygulanmadı. ...").
- "sonuc": çözüldüyse nasıl doğrulandığını yaz; açık kaldıysa "Sorun devam ediyor." veya "Konu açık." gibi belirt. Müşteri onayı alındıysa ekle.
- "sonraki": takip yoksa "Ek bir işlem gerekmiyor, kayıt kapatılabilir." yaz; takip varsa kim, neyi, ne zaman yapacak yaz.
- "ucret": notta ücret veya ücretsiz olma gerekçesi geçiyorsa onu düzgün cümleyle yaz; geçmiyorsa aynen şunu yaz: "<VARSAYILAN_UCRET>"
- "kayit": notta aksi belirtilmedikçe "<VARSAYILAN_KAYIT>" yaz.

Yalnızca şu anahtarları içeren geçerli bir JSON nesnesi döndür, başka hiçbir şey yazma:
{"cozum": "...", "sonuc": "...", "ozet": "...", "kontroller": "...", "kok_neden": "...", "sonraki": "...", "ucret": "...", "kayit": "..."}

Aşağıda aynı personelin daha önce onayladığı örnekler var. Üslubu, uzunluğu ve yorumlama şeklini bunlarla aynı tut.
"""


def system_prompt(cfg):
    parts = [KURALLAR]
    for i, (not_, cikti) in enumerate(ORNEKLER, 1):
        parts.append(f"\nÖrnek {i} - Not:\n{not_}\nÇıktı:\n{json.dumps(cikti, ensure_ascii=False)}\n")
    text = "".join(parts)
    return (text.replace("<VARSAYILAN_UCRET>", cfg["varsayilan_ucret"])
                .replace("<VARSAYILAN_KAYIT>", cfg["varsayilan_kayit"]))

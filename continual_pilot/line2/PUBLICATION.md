# Hat 2 arşivinin dışa aktarımı

Hazırlık tarihi: 2026-09-16.
Bu belge yayımlama hazırlığını kaydeder; tek başına başarılı gönderim
veya doğrulanmış Bitcoin zaman damgası kanıtı değildir.

## Korunan ilk kayıt

İlk yerel commit:
29f224ac169a67516b484f1446a3532ca324c128

[Kilitli revizyon 1](PREREGISTRATION_DRAFT.md) değişmemiştir.
Protokolün ham bayt SHA-256 özeti:
0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7

[Tarihli yerel kilit özeti](LOCK_2026-09-16.md) tarihsel kayıt olarak korunur.
O belgedeki “uzak gönderim kapsam dışı” ifadesi ilk kilitleme turuna aittir;
kullanıcı sonraki turda GitHub dışa aktarımını ayrıca onaylamıştır.

## Taşınabilirlik ve lisans

Depo köküne [MIT lisansı](../../LICENSE) eklenmiştir.
Aşağıdaki tarihsel raporlarda yalnızca çıktı dizini metaverisi,
çalışma alanı köküne göre göreli yol olacak şekilde değiştirilmiştir:

- [Eski tanı raporu](../results_diagnose/summary.json)
- [Birleşik öğrenci raporu](../results_v02/summary.json)
- [v0.2 jeneratör raporu](../results_generator_v02/summary.json)
- [v0.3 jeneratör raporu](../results_generator_v03/summary.json)

Ölçümler, tohumlar, kararlar ve model kayıtları bu düzenlemeyle değiştirilmez.
Bu dört dosyanın bayt özetleri metaveri değişikliği nedeniyle farklıdır.
Özgün sürümleri ilk commit üzerinden erişilebilir kalır.
İlk commit yeniden yazılmadığı için eski mutlak yollar Git geçmişinde
bulunmaya devam eder; bu işlem geçmişten kişisel veri silme işlemi değildir.
Git commit yazar bilgileri de geçmişin parçasıdır.

## OpenTimestamps makbuzu

[Makbuz](PREREGISTRATION_DRAFT.md.ots), kilitli protokol dosyasının
SHA-256 taahhüdü için alınmıştır. Belgenin kendisi takvime yüklenmemiştir;
rastgele nonce eklenmiş kriptografik taahhüt gönderilmiştir.

İlk makbuzun SHA-256 özeti:
7ded550e25972aa61660ce10d9519cf1f32fc37db9f8918c90ca039c3cec2de3

2026-09-16 tarihinde makbuz ayrıştırılarak belge hash'i ile eşleşmesi
kontrol edildi. Yanıt alınan gönderim hizmeti:
https://b.pool.opentimestamps.org

Makbuzdaki bekleyen takvim:
https://bob.btc.calendar.opentimestamps.org

İlk durum: **takvim kabulü mevcut; Bitcoin zincir doğrulaması yapılmadı**.
Makbuzun geçerli biçimde ayrıştırılması, zincire dahil olma veya belirli
bir tarihten önce varlık kanıtının bağımsız doğrulanması anlamına gelmez.
Yükseltilmiş makbuz alınırsa makbuz dosyası özeti değişebilir;
protokolün kilitli hash'i değişmemelidir. Doğrulama sonucu ayrıca kaydedilir.

İlk takvim isteği süresi dolmuş TLS sertifikası nedeniyle reddedildi;
sertifika doğrulaması devre dışı bırakılmadı.
Windows CLI bağımlılık sorunu nedeniyle kurulu OpenTimestamps kütüphanesinin
takvime gönderim ve standart makbuz serileştirme API'si kullanıldı.
Kütüphane kriptografik kontrolleri veya bağımlılık kaynakları değiştirilmedi.

## Bu turun sınırı

GitHub gönderimi ve damga durumu doğrulanmadan veri üreten deney başlamaz.
Sonraki izin yalnızca Hat 2 uygulama/testleri ve v0.4 kabul–kapı kontrolleridir.
Süre pilotu, güç pilotu ve ana deney bu izin kapsamında değildir.
GitHub'a gönderim ve Bitcoin doğrulaması tamamlandığında gerçek kimlikler
ve durumları ayrıca raporlanır; hazırlık adımları başarı olarak sunulmaz.
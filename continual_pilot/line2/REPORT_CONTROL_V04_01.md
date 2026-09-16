# v0.4 kontrol turu — kabul başarısızlığında durma

Rapor tarihi: 2026-09-16.

## Sonuç

10000–10199 öğretmen tohumları artan sırayla sınandı.
**200 adaydan 0 kabul; gerekli üç jeneratör bulunamadı.**
Öğrenilebilirlik kapısı ve bütün sonraki deneyler başlatılmadı.
Bu, mevcut tasarımın incelenen havuzda başarısızlığıdır;
uygun bir jeneratörün matematiksel olarak imkânsız olduğunu göstermez.

## Önkayıt, test ve kaynak yedeği

- [Kilitli protokol](PREREGISTRATION_DRAFT.md) değiştirilmedi.
- Protokol SHA-256:
  0800b0647a0feec22dc13b83ddfaaa7478dc4cd8fe54d3a923423f3cd8d136f7
- [Onaylı uygulama eki](IMPLEMENTATION_ADDENDUM_2026-09-16.md) SHA-256:
  f7e8e9c441a4673894e01aa2dd9ee481d4882bfb5f5ae04f79a0d2c7f1c9ef98
- [Kaynağa bağlı doğrulama kaydı](validation_2026-09-16_01.json):
  112 mekanik test geçti; kayıtlı test günlüğü süresi 6,186 saniye.
- Koşu öncesinde uzak dal ile eşleşmesi doğrulanan kaynak commit'i:
  fb9bb97c04b58efadb8e8855e2604b8969c93adc.
- GitHub: https://github.com/FearmessOp/continual-pilot
  Özel depo, MIT lisansı.
- Test başarısı bütün araştırma protokolünün eksiksiz uygulandığının
  veya yöntemlerin bilimsel başarısının kanıtı değildir.

## Kabul ölçümleri

İki kuralda birlikte normalize marj ≥0,25 filtresi kullanıldı.
Ölçekler bağımsız, filtresiz eşit M1/M2 kalibrasyonundan hesaplandı.
Ofsetler filtre sonrasında yeniden ayarlanmadı.
Dışlama tavanı her karışım için %30; sınıf bandı %18–35;
uyuşmazlık bandı %40–70 olarak korundu.

| Aday düzeyindeki red birleşimi | Sayı |
|---|---:|
| Yalnız dışlama | 39 |
| Denge ve dışlama | 156 |
| Denge, uyuşmazlık ve dışlama | 5 |
| Toplam | 200 |

Kriter başına aday sayıları örtüşür:
dışlama 200, denge 161, uyuşmazlık 5.
Teklif bütçesi tükenmesine bağlı red yoktur.

Her aday/karışım için dışlama 100.000 teklif üzerinde;
denge ve uyuşmazlık ayrı akışta 20.000 kabul edilmiş örnekte ölçüldü.

| Ölçüm | M1 | M2 |
|---|---:|---:|
| En düşük dışlama (%) | 30,080 | 28,113 |
| Medyan dışlama (%) | 46,2445 | 46,263 |
| Ortalama dışlama (%) | 46,641785 | 46,608215 |
| En yüksek dışlama (%) | 65,368 | 59,631 |
| Dışlama ihlali olan aday | 200 | 199 |
| Denge ihlali olan aday | 117 | 124 |
| Uyuşmazlık ihlali olan aday | 4 | 3 |
| 20.000 kabul için en az teklif | 28.499 | 27.822 |
| 20.000 kabul için en çok teklif | 58.326 | 49.614 |

M1'deki en düşük dışlama bile %30 tavanının üzerindedir.
%30,080 aşağı yuvarlanarak kabul edilmedi.

## Çalıştırılmayan kontroller

| Aşama veya ölçüm | Durum |
|---|---|
| A, R1/M1 ve R2/M2 öğrenilebilirlik kapısı | Kabul önkoşulu sağlanmadı; çalıştırılmadı |
| C ve ideal-D uzman kontrolleri | Çalıştırılmadı |
| Ölçülmüş kapı eşikleri ve Wilson aralıkları | Üretilmedi |
| Öğrenci karışıklık matrisleri ve öğrenme eğrileri | Üretilmedi |
| CPR son-64-adım medyan etkinliği | Ölçülmedi |
| Temsil tanısı ve B/D durağan sistem kaybı | Ölçülmedi |
| Süre pilotu, güç pilotu ve ana deney | Başlatılmadı |

Kapının çalıştırılmaması kapının başarısız olduğu anlamına gelmez.
Başarısız aşama jeneratör kabulüdür.

## Süre ve kayıt bütünlüğü

- Kabul süresi: 481,5461724 saniye.
- Yürütücü içi toplam duvar süresi: 482,1330242 saniye,
  yaklaşık 8 dakika 2 saniye.
  Son manifest doğrulama/yazma süresi bu ölçümün dışında kalabilir.
- Tamamlanma kaydı: 2026-09-16T16:01:43.267947Z.
- Manifestteki 3.650 dosyanın SHA-256 ve boyutları koşu sonrasında
  diskten tekrar doğrulandı.
- Manifest hariç toplam: 5.832.109.949 bayt (5,431575653 GiB).
- En büyük tek dosya: 7.842.848 bayt.
- [Manifest](results_control_v04_01/manifest.json) SHA-256:
  2c37cd3ff958c0fae9f0a7983958bdd85ba924de4af41fe796b4391baa89c29d
- [Kabul özeti](results_control_v04_01/acceptance_summary.json),
  [aşama özeti](results_control_v04_01/summary.json) ve
  [yürütme kaydı](results_control_v04_01/execution.json) korunur.
- Ham sonuç arşivinin dış yedeği bu rapor yazılırken henüz doğrulanmadı.
  Kaynakların gönderilmiş olması sonuçların da gönderildiği anlamına gelmez.
- Yerel CPU koşusunun parasal maliyeti ölçülmedi.
  Arayüzdeki birikimli API tutarı bu deneyin hesaplama maliyeti değildir.

## OpenTimestamps ve güncel izin

Özgün [makbuz](PREREGISTRATION_DRAFT.md.ots) uzak kaynak deposundadır.
Son takvim kontrolü 2026-09-16T15:16:01.565462Z:
“Pending confirmation in Bitcoin blockchain”.
O kontrolde Bitcoin blok tasdiki alınmadı, zincir doğrulaması yapılmadı.
Bu rapor daha yeni bir Bitcoin onayı iddia etmez.
Kullanıcı, onaylı uygulama ekinde bekleyen makbuzun kabul/kapıyı
tek başına engellemediğini açıkça belirtti.
[Yayımlama notundaki](PUBLICATION.md) önceki önkoşul ifadeleri
bu sonraki kullanıcı onayıyla birlikte okunmalıdır.

## Durma kararı

Aday havuzu genişletilmedi; filtre, ofset ve kabul bantları değiştirilmedi.
Yeni deney veya ayar araması başlatılmaz.
Sonraki bilimsel adım gerekçeli yeni revizyon ve kullanıcı kararı gerektirir.
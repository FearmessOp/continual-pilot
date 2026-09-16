# Kısaltılmış asimetrik pilot — sonuç öncesi protokol

Keşiften türetilmiş pilot; hipotez testi değil.
v0.3 öğrencisinin öğrenilebilirlik kapısı geçilmedi.
Bu tur yalnızca aşağıdaki iki adayı çalıştırır; Hat 2 başlatılmaz.

## Önceki protokolden açık farklar

Önceki pilot 2.000/4.000 adayları ve %80 başlangıç öğrenimi kontrolü
kullanıyordu. Hiçbir aday seçilmedi. Kısaltılmış adaylar ve %86 kontrolü
bu yeni turun kararlarıdır; geçmişte önkayıtlanmış gibi sunulmaz.
Eski protokol, kaynaklar ve sonuçlar değiştirilmez.

## Sabit ayarlar

- Jeneratör v0.3; öğretmen tohumu 1000, paylaşım 0,5, gürültü %5.
- Öğrenci 32→64→4, ReLU, bağlamsız; başlangıç tohumu 7.
- Adam, sabit öğrenme oranı 0,001; minibatch 16 yeni örnek.
- Yöntemler A ve replay. Uniform reservoir kapasitesi 512;
  her yeni örnek için en fazla 8 geçmiş örnek.
- Replay dahil tüm grup örnekleri eşit ağırlıklı kayıpla eğitilir.
  En fazla 144 örnek/güncelleme; hesaplama bütçeleri eşit değildir.
- Akış tohumları 240001, 240002, 240003; model başlangıcı ve jeneratör sabit.
- Fazlar M1/R1 → M2/R1 → M2/R2 → M2/R1.
- Faz 1/2/4 uzunlukları 40.000 / 10.000 / 4.000.
- Faz 3 adayları 1.024 ve 1.536: tam 64 ve 96 güncelleme.
- D480: faz 4 ilk 480 yeni örnek, tam 30 güncelleme; tanım değişmez.
- Değerlendirme: bağımsız 249001 tohumu, 20.000 M2 girdisi,
  aynı girdiler üzerinde R1 ve R2 temiz hedefleri.

Her akış tohumu s için faz tohumları s, s+1000, s+2000, s+3000;
reservoir değiştirme/örnekleme tohumları s+4000 ve s+4001.
Bu düzen önceki pilotla aynıdır. Ardışık akış tohumları nedeniyle farklı
koşuların reservoir değiştirme ve örnekleme tohumları örtüşebilir;
tüm rastgelelik kaynaklarının koşular arasında bağımsız olduğu iddia edilmez.

Faz 3 bir kez 1.536 örnek üretilir; kısa aday ilk 1.024 örneği kullanır.
Faz 4 iki adaya ortaktır. Faz 2 sonunda model, optimizer, tampon ve iki
RNG durumu birlikte kopyalanır; adaylar aynı durumdan devam eder.
A ve replay aynı başlangıç ağırlıkları ve verilerle eşleştirilir.
Güncel tahmin etiketten önce yapılır; temiz etiketler eğitimde kullanılmaz.

## Ölçümler ve seçim

Faz 2/3/4 sonu donmuş modeller aynı değerlendirmede R1 ve R2'ye karşı ölçülür.
Hasar = faz2 R1 doğruluğu − faz3 R1 doğruluğu.
Toparlanma = faz4 R1 doğruluğu − faz3 R1 doğruluğu.
D480 = faz4 çevrimiçi temiz hata sayısı − kendi faz2 donmuş modelinin
aynı 480 girdideki temiz hata sayısı. D480/480 ayrıca raporlanır.
Her faz için örnek/güncelleme sayısı, toplam ve örnek başına kâhin
pişmanlığı, replay örnek sayısı saklanır.

Karar yalnızca A'nın üç akıştaki donmuş ölçümlerinden alınır:
1. Üç akışın tümünde faz2 R1 doğruluğu en az %86 olmalı.
   Sağlanmazsa başlangıç kontrolü başarısızdır; süre seçilmez,
   otomatik sonraki aday önerilmez. Bu kontrol öğrenilebilirlik kapısı değildir.
2. Üç akışın tümünde hasarı kapalı 20–40 yüzde puanı bandında olan
   en kısa aday seçilir. Replay sonuçları seçim koşulu değildir.
3. Uygun aday yok ve her iki adayın üç akıştaki tüm hasarları 20 puanın
   kesin olarak altındaysa gelecek ayrı tur için 1.792 (112 güncelleme) önerilir.
4. Uygun aday yok ve aynı altı hasarın tümü 40 puanın kesin olarak
   üstündeyse gelecek ayrı tur için 768 (48 güncelleme) önerilir.
5. Diğer karışık sonuçlarda aday seçilmez ve otomatik öneri yapılmaz.

1.792 veya 768 bu turda eğitilmez. Bant genişletilmez, yuvarlamayla kabul
yapılmaz. Eksik/tekrarlı sonuç satırları karar üretmek yerine hata verir.
Seçim varsa yalnızca v0.3 pilotuna aittir; v0.4'e otomatik aktarılmaz.

## Öngörü, seçim koşulu değil

Kullanıcının öngörüsü: 1.024 örnekte yaklaşık 16–20 puan,
1.536 örnekte yaklaşık 28–32 puan hasar.
Bunlar gözlem değil; yukarıdaki seçim kuralını değiştirmez.

## Hat 2'ye kaydedilen ölçüm kısıtı

Yeni-kural öğrenimi ve eski-kural korunması birlikte raporlanmalıdır:
faz3 sonu R2 doğruluğu ile faz4 R1 performansı, faz2 referansından
hasar ve toparlanma bilgisiyle birlikte gösterilir.
Tek D480 değeriyle üstünlük veya kazanan ilan edilmez.
Düşük D480 ile düşük R2 doğruluğu, daha az öğrenerek daha az unutma
açıklamasıyla uyumlu olabilir; tek başına nedensel kanıt değildir.

Mekanizma hiperparametreleri ayrı tek-rejim kontrollerinde sabitlenir.
64 güncellemede tepkisizlik olası sonuçtur; sonuç görülünce ayar
değiştirilerek örtülmez. Bu pilot yönlendirme, CPR, k-NN veya ana 2×2'yi
çalıştırmaz. Hat 2'de bunlar ayrı önkayıt ve doğrulama gerektirir.

## Kayıt politikası

Eski eğitim çekirdeği yeniden kullanılır; mevcut yapılandırması değiştirilmez.
Yeni protokol ve kaynakların koşu öncesi kopyaları alınır.
Girdiler, gizli örnekler, hedefler, örnek sırası, çevrimiçi/donmuş tahminler,
D480 referansı ve model/optimizer/tampon/RNG kontrol noktaları saklanır.
Dosya bütünlük ve yükleme kontrolleri zorunludur.
Mevcut çıktı dizinine yazılmaz; başarısızlıkta sonuçlar sessizce değiştirilmez.
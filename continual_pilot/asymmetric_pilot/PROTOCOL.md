# Asimetrik faz uzunluğu pilotu — sonuç öncesi protokol

Durum: Uygulama ve eğitim öncesinde kaydedildi.
Etiket: Keşiften türetilmiş faz uzunluğu pilotu; hipotez testi değil.
v0.3 temel öğrencisinin öğrenilebilirlik kapısı geçilmedi.
Önceki sonuçlar korunur; bu tur Hat 2 veya v0.4 çalıştırmaz.

## Sabit düzen

- Jeneratör: v0.3, öğretmen tohumu 1000, paylaşım 0,5, etiket gürültüsü %5.
- Öğrenci: 32→64→4, ReLU, bağlam yok; başlangıç tohumu 7.
- Optimizasyon: Adam, sabit öğrenme oranı 0,001, minibatch 16 yeni örnek.
- Yöntemler: A ve uniform reservoir replay; kapasite 512.
- Replay her yeni tahminden sonra, güncel örnek tampona eklenmeden önce
  en fazla 8 geçmiş örnek çeker. 16 yeni örnek ve bunların replay örnekleri
  tek eşit-ağırlıklı kayıpla güncellenir; en fazla 144 örnek/güncelleme.
- Tampon, optimizer ve öğrenci faz sınırında sıfırlanmaz.
- Güncel tahmin güncel etiketten önce yapılır. Temiz etiket öğrenciye verilmez.
- Üç akış tohumu: 230001, 230002, 230003.
- Başlangıç tohumu sabittir: bunlar üç model başlangıcı veya jeneratör değildir.

| Faz | Karışım/kural | Örnek | Güncelleme |
|---|---|---:|---:|
| 1 | M1/R1 | 40.000 | 2.500 |
| 2 | M2/R1 | 10.000 | 625 |
| 3 | M2/R2 | 2.000 veya 4.000 | 125 veya 250 |
| 4 | M2/R1 | 4.000 | 250 |

## Akış ve dallanma eşleştirmesi

Her akış tohumu s için faz 1/2/3/4 tohumları sırasıyla
s, s+1000, s+2000, s+3000; reservoir değiştirme tohumu s+4000,
reservoir örnekleme tohumu s+4001 olur. Bu tohum kümeleri çakışmaz.
Faz 3 önce 4.000 örnek olarak üretilir; kısa aday ilk 2.000 örneği kullanır.
Faz 4 verileri iki aday ve iki yöntemde aynıdır.
A ve replay aynı başlangıç ağırlıklarının ayrı kopyalarıyla başlar.
Her yöntemin faz 2 sonu model, optimizer, tampon ve iki RNG durumu birlikte
kopyalanır; iki aday bu aynı durumdan ayrı ayrı devam eder.
Adaylar aynı faz-3 önekinde aynı tahminleri üretmelidir.
Dallanma ve dondurulmuş değerlendirme kaynak durumu değiştirmemelidir.

## Ölçümler

Bağımsız değerlendirme: tohum 239001, M2'den 20.000 ortak girdi.
Her girdide değerlendirici R1 ve R2 temiz hedeflerini üretir.
Faz 2/3/4 sonu modelleri aynı girdilerde her iki kurala karşı ölçülür.
Hasar = faz2 R1 doğruluğu − faz3 R1 doğruluğu.
Toparlanma = faz4 R1 doğruluğu − faz3 R1 doğruluğu.
Faz 3 R2 doğruluğu yeni kurala uyumu ayrıca gösterir.

Geçiş penceresi: faz 4'ün ilk 30 güncellemesi, yani 480 yeni örnek.
D480 = çevrimiçi modelin temiz hata sayısı − kendi faz2 donmuş kopyasının
aynı 480 girdideki temiz hata sayısı. D480 ve D480/480 birlikte raporlanır.
D1000 tarihsel metrik olarak kalır; yeniden adlandırılmaz.
Her faz için örnek sayısı, gerçek güncelleme sayısı, temiz/gürültülü doğruluk,
toplam ve örnek başına kâhin pişmanlığı, işlenen replay örneği sayısı verilir.
A ve replay için güncelleme sayısı eşitliği hesaplama eşitliği değildir.

## Önceden belirlenen seçim

Seçim yalnızca A'nın donmuş ölçümleri üzerinden yapılır.
Üç akışın tümünde faz2 R1 temiz doğruluğu en az %80 olmalıdır.
Bu, yeterli başlangıç öğrenimi için pilot kontrolüdür; öğrenilebilirlik kapısı değil.
Uygunluk sağlanırsa üç akışın tümünde hasarı 20–40 yüzde puanı
(kapalı aralık) olan en kısa aday seçilir. İkisi de uymazsa aday seçilmez.
Eşikler genişletilmez, yeni aday otomatik eklenmez; replay sonucu seçimi belirlemez.
Seçim yalnızca bu v0.3 pilotuna aittir; filtreli v0.4'e otomatik aktarılmaz.
Önceki 40k+40k hazırlık eğrisinden farklı olarak faz 2 burada 10k'dır;
önceki eğriler bu pilotun sonucunu garanti etmez.

## Kalıcı kayıt ve kapsam

Her fazın girdileri, tam hassasiyetli gizli örnekleri, gürültülü/temiz hedefleri,
örnek sırası ve tüm çevrimiçi tahminler saklanır. Faz2/3/4 ağırlıkları,
optimizer/tampon/RNG kontrol noktaları, donmuş tahminler ve D480 referans
tahminleri kaydedilir. Dosya özetleri ve yükleme doğrulaması zorunludur.
Protokol ve kaynak dosyalarının koşu öncesi kopyaları saklanır.
Var olan çıktı dizininin üzerine yazılmaz.

Hat 2'de yakın-pencereli k-NN rakibi ve CPR-tarzı sürekli kısmi çekme
yenilemesi ayrı spesifikasyon gerektirir; bu pilotta uygulanmaz.
256 örneklik pencerenin yenilenmesi 256 örnekte yüksek doğruluk garantisi değildir.
Rejim etiketi yalnızca değerlendiricide tutulan replay çatışma tanısı ana
2×2 dışında kalır; korelasyon tek başına nedensel kanıt sayılmaz.
Öğretmen uyumuna yakın doğruluk tam bilgi kaybını kanıtlamaz; etkileşimde
taban etkisi riski vardır, fakat etkileşimin sıfıra çökmesi kanıtlanmış değildir.
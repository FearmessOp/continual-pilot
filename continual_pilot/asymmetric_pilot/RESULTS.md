# Asimetrik faz uzunluğu pilotu — sonuç

**Keşiften türetilmiş pilot; hipotez testi değil. Öğrenilebilirlik kapısı geçilmedi.**
[Sonuç öncesi protokol](PROTOCOL.md) ve [tam sayısal rapor](results/summary.json).

## Karar: aday seçilmedi

A'nın faz 2 M2/R1 temiz doğrulukları %86,540, %87,170 ve %86,900:
üçü de pilotun %80 başlangıç öğrenimi kontrolünü geçti.
Bu kontrol öğrenilebilirlik kapısının yerine geçmez.

Seçim yalnızca A'nın üç akışın tümünde 20–40 yüzde puanı hasar bandını
sağlamasına bağlıydı:

- **2.000 örnek / 125 güncelleme:** 37,825 / 38,160 / 40,550 puan.
  İlk iki akış uygun, üçüncü akış üst sınırı 0,550 puan aşıyor.
- **4.000 örnek / 250 güncelleme:** 41,875 / 43,550 / 42,925 puan.
  Üç akış da üst sınırı aşıyor.

Dolayısıyla uygun aday kümesi boş. Yuvarlamayla kabul, bant genişletme
veya sonuç sonrası yeni aday ekleme yapılmadı. Bu, kısa fazların imkânsız
olduğu anlamına gelmez; yalnızca sınanan iki adayın sabit seçim kuralını
sağlamadığını gösterir. 2.000 örnek Hat 2 için seçilmiş süre değildir.

## Donmuş ölçümler ve geçiş bedeli

Tüm doğruluklar aynı 20.000 bağımsız M2 girdisinde ölçüldü.
F2/F3/F4, ilgili faz sonu modelinin **R1 temiz doğruluğu**; F3–R2,
faz 3 sonu modelinin **R2 temiz doğruluğudur**.
Hasar = F2−F3; toparlanma = F4−F3. İkisi de yüzde puanı cinsindendir.
D480, faz 4 ilk 480 örneğinde kendi faz 2 donmuş referansına göre ek temiz hatadır.

| Akış tohumu | Yöntem | F3 örnek | F2 R1 % | F3 R1 % | F4 R1 % | F3 R2 % | Hasar (puan) | Toparlanma (puan) | D480 | D480/480 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 230001 | A | 2000 | 86,540 | 48,715 | 86,400 | 72,965 | 37,825 | 37,685 | 145 | 0,30208 |
| 230001 | A | 4000 | 86,540 | 44,665 | 86,020 | 78,845 | 41,875 | 41,355 | 161 | 0,33542 |
| 230001 | replay | 2000 | 82,285 | 78,420 | 82,725 | 44,085 | 3,865 | 4,305 | 13 | 0,02708 |
| 230001 | replay | 4000 | 82,285 | 77,335 | 80,895 | 45,390 | 4,950 | 3,560 | 16 | 0,03333 |
| 230002 | A | 2000 | 87,170 | 49,010 | 86,195 | 74,100 | 38,160 | 37,185 | 150 | 0,31250 |
| 230002 | A | 4000 | 87,170 | 43,620 | 85,535 | 77,935 | 43,550 | 41,915 | 174 | 0,36250 |
| 230002 | replay | 2000 | 81,270 | 77,860 | 80,245 | 47,540 | 3,410 | 2,385 | 24 | 0,05000 |
| 230002 | replay | 4000 | 81,270 | 75,095 | 80,310 | 49,850 | 6,175 | 5,215 | 26 | 0,05417 |
| 230003 | A | 2000 | 86,900 | 46,350 | 85,030 | 74,940 | 40,550 | 38,680 | 172 | 0,35833 |
| 230003 | A | 4000 | 86,900 | 43,975 | 84,790 | 78,455 | 42,925 | 40,815 | 193 | 0,40208 |
| 230003 | replay | 2000 | 82,000 | 79,055 | 80,770 | 43,370 | 2,945 | 1,715 | 8 | 0,01667 |
| 230003 | replay | 4000 | 82,000 | 79,005 | 80,060 | 44,540 | 2,995 | 1,055 | 10 | 0,02083 |

## Faz başına örnek başına kâhin pişmanlığı

Bu değerler öğrenci gürültülü hata sayısı eksi kâhin gürültülü hata
sayısının fazdaki örnek sayısına bölümüdür; temiz hata oranı değildir.
Ham toplamlar da [sayısal raporda](results/summary.json) saklanır.
İki adayın ortak faz 1–2 değerleri tabloda tekrar gösterilmiştir;
bunlar ayrı eğitim tekrarları değildir.

| Akış | Yöntem | F3 örnek | F1 | F2 | F3 | F4 |
|---|---|---:|---:|---:|---:|---:|
| 230001 | A | 2000 | 0,158500 | 0,134200 | 0,372000 | 0,197000 |
| 230001 | A | 4000 | 0,158500 | 0,134200 | 0,289500 | 0,217750 |
| 230001 | replay | 2000 | 0,169275 | 0,170400 | 0,531000 | 0,156500 |
| 230001 | replay | 4000 | 0,169275 | 0,170400 | 0,520250 | 0,178250 |
| 230002 | A | 2000 | 0,156525 | 0,124400 | 0,369000 | 0,192000 |
| 230002 | A | 4000 | 0,156525 | 0,124400 | 0,298500 | 0,214750 |
| 230002 | replay | 2000 | 0,165000 | 0,156700 | 0,502500 | 0,179500 |
| 230002 | replay | 4000 | 0,165000 | 0,156700 | 0,493500 | 0,186750 |
| 230003 | A | 2000 | 0,161900 | 0,135800 | 0,351500 | 0,197750 |
| 230003 | A | 4000 | 0,161900 | 0,135800 | 0,285750 | 0,209000 |
| 230003 | replay | 2000 | 0,169200 | 0,173400 | 0,544500 | 0,174000 |
| 230003 | replay | 4000 | 0,169200 | 0,173400 | 0,535000 | 0,179250 |

## Güncelleme bütçesi ve eşleştirme

- Faz 1: 40.000 örnek, 2.500 güncelleme.
- Faz 2: 10.000 örnek, 625 güncelleme.
- Faz 3: 2.000/4.000 örnek, 125/250 güncelleme.
- Faz 4: 4.000 örnek, 250 güncelleme.
- Her adayın faz 4 geçiş penceresi: **480 örnek, tam 30 güncelleme**.
- Faz 2'den itibaren dallanma dahil tam yol: 56.000/58.000 örnek,
  3.500/3.625 toplam güncelleme. Ortak faz 1–2 yalnızca bir kez eğitildi.

Replay her yeni örnek için en fazla 8 geçmiş örnek kullanır.
Faz 3'te A 2.000/4.000 eğitim örneği işlerken replay tekrarlar dahil
18.000/36.000 örnek işler. Güncelleme sayısı eşitliği hesaplama veya
bellek eşitliği değildir.

Altı yöntem–akış çiftinde faz 2 kaynak durumu değişmeden kaldı;
iki adayın faz 3 ortak önek tahminleri birebir eşleşti.
Başlangıç modeli tohumu 7, jeneratör tohumu 1000 sabittir.
Bu sonuçlar üç akış üzerinden elde edilmiştir; üç farklı model
başlangıcı veya üç farklı jeneratör üzerinden değil.

## Yorum sınırları

A'da daha uzun R2 eğitimi daha yüksek R2 doğruluğu, daha yüksek R1 hasarı
ve daha yüksek D480 ile birlikte görüldü. Replay daha az R1 kaybetti,
ancak F3–R2 doğruluğu %43,370–%49,850 arasında kaldı.
Bu nedenle düşük D480 tek başına daha iyi sürekli öğrenme kanıtı değildir.
Her yöntem kendi faz 2 referansına göre ölçülür; referans seviyeleri de farklıdır.

Pilotun %80 başlangıç kontrolü sağlandı, öğrenilebilirlik kapısı ise
geçilmiş değildir. %40,550 hasarı %40'a yuvarlayarak kabul etmek,
ölçüm belirsizliği gerekçesiyle sınırı değiştirmek veya yalnızca başarılı
iki akışı seçmek bu protokole aykırı olur.
Bununla birlikte 0,550 puanlık sınır aşımı genel bir imkânsızlık veya
istatistiksel anlamlılık iddiası değildir.

Önceki çevrimiçi eğriler 40k+40k hazırlık sonrası ölçülmüştü;
bu pilot 40k+10k hazırlık ve yeni akış tohumları kullandı.
Bu yüzden eski bloklardan okunan aralıkların tam uymaması çelişki değildir.
Hat 2'ye aktarılacak faz uzunluğu bu turda sabitlenemedi.
Yeni aday veya karar kuralı ayrı bir pilot protokolü gerektirir.

## Kayıt ve testler

Yeni pilotun **8 ilgili testi geçti**; bu tur tüm eski test paketi yeniden
çalıştırılmadı. Kontrol noktası yükleme sonrası aynı şekilde eğitime
devam etme, tam durumdan dallanma, nedensel tahmin sırası, güncelleme sayıları,
normalize ölçümler ve seçim kuralı test edildi.

[Koşu manifesti](results/manifest.json) tüm kayıt dosyalarının SHA-256
özetlerini içerir. Girdiler, gizli örnekler, temiz/gürültülü hedefler,
örnek sırası, çevrimiçi/donmuş tahminler ve D480 referansı saklandı.
Model, optimizer, reservoir ve RNG durumları yüklenerek doğrulandı;
protokol ve kaynak dosyalarının koşu öncesi kopyaları korundu.
Eski deney dosyaları değiştirilmedi.

**Hat 2, v0.4, k-NN, CPR ve yönlendirme bu turda çalıştırılmadı.**
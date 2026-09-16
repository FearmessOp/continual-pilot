# Kısaltılmış pilot sonucu: 1.024 örnek seçildi

**Keşiften türetilmiş pilot; hipotez testi değil. Öğrenilebilirlik kapısı geçilmedi.**

[Sonuç öncesi protokol](PROTOCOL.md), [tam sayısal rapor](results/summary.json)
ve [kayıt bütünlüğü manifesti](results/manifest.json).

## Seçim kararı

A'nın faz-2 M2/R1 temiz doğruluğu üç akışta %86,400 / %86,610 / %87,160:
yeni protokolün en az %86 başlangıç kontrolü sağlandı.
Bu kontrol, öğrenilebilirlik kapısının yerine geçmez.

| Akış tohumu | 1.024 örnekte hasar (puan) | 1.536 örnekte hasar (puan) |
|---|---:|---:|
| 240001 | 24,870 | 32,970 |
| 240002 | 26,190 | 35,890 |
| 240003 | 28,500 | 34,555 |

Her iki aday üç akışın tümünde kapalı 20–40 yüzde puanı bandında kaldı.
Önceden sabitlenen en kısa uygun aday kuralıyla **1.024 örnek / 64 güncelleme**
seçildi. 1.536 örnek / 96 güncelleme de uygundu; sonuçlara göre yeni bir
tercih ölçütü eklenmedi. 1.792 ve 768 öneri dalları tetiklenmedi, çalıştırılmadı.

Bu karar yalnızca v0.3 pilotuna aittir; filtreli v0.4'e otomatik aktarılmaz.
Önceki pilotun %80 kontrolü ve 2.000/4.000 adayları tarihsel kayıtta korundu;
bu turun %86 kontrolü geriye dönük uygulanmadı.

## Donmuş doğruluklar ve geçiş bedeli

F2/F3/F4 sütunları ilgili faz sonu modelinin aynı bağımsız 20.000 M2
girdisinde R1 temiz doğruluğudur. F3–R2 aynı faz-3 modelinin yeni kurala
karşı doğruluğudur. Hasar = F2−F3; toparlanma = F4−F3, yüzde puanı cinsinden.

D480, faz 4 ilk 480 örneğinde çevrimiçi temiz hata sayısı eksi kendi
faz-2 donmuş referansının aynı örneklerdeki temiz hata sayısıdır.
Her satırda pencere tam 30 güncelleme içerir.

| Akış | Yöntem | F3 örnek | F2 R1 % | F3 R1 % | F4 R1 % | F3 R2 % | Hasar (puan) | Toparlanma (puan) | D480 | D480/480 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 240001 | A | 1024 | 86,400 | 61,530 | 86,380 | 63,225 | 24,870 | 24,850 | 107 | 0,22292 |
| 240001 | A | 1536 | 86,400 | 53,430 | 86,415 | 70,825 | 32,970 | 32,985 | 135 | 0,28125 |
| 240001 | replay | 1024 | 82,010 | 78,410 | 80,905 | 43,505 | 3,600 | 2,495 | 19 | 0,03958 |
| 240001 | replay | 1536 | 82,010 | 78,390 | 80,395 | 43,550 | 3,620 | 2,005 | 13 | 0,02708 |
| 240002 | A | 1024 | 86,610 | 60,420 | 86,395 | 64,445 | 26,190 | 25,975 | 101 | 0,21042 |
| 240002 | A | 1536 | 86,610 | 50,720 | 86,220 | 71,740 | 35,890 | 35,500 | 131 | 0,27292 |
| 240002 | replay | 1024 | 82,105 | 80,400 | 81,315 | 43,020 | 1,705 | 0,915 | 12 | 0,02500 |
| 240002 | replay | 1536 | 82,105 | 78,960 | 80,830 | 44,615 | 3,145 | 1,870 | 13 | 0,02708 |
| 240003 | A | 1024 | 87,160 | 58,660 | 87,225 | 63,060 | 28,500 | 28,565 | 129 | 0,26875 |
| 240003 | A | 1536 | 87,160 | 52,605 | 87,020 | 68,775 | 34,555 | 34,415 | 149 | 0,31042 |
| 240003 | replay | 1024 | 82,555 | 79,275 | 82,050 | 44,145 | 3,280 | 2,775 | 16 | 0,03333 |
| 240003 | replay | 1536 | 82,555 | 78,555 | 82,170 | 45,210 | 4,000 | 3,615 | 20 | 0,04167 |

## Örnek başına kâhin pişmanlığı

Gürültülü etiketlerde öğrenci hata sayısı ile kâhin hata sayısının farkı,
faz örnek sayısına bölünmüştür. Temiz hata oranı değildir.
Ham toplamlar da [sayısal raporda](results/summary.json) bulunur.
Ortak faz 1–2 sonuçlarının iki adayda tekrarı bağımsız eğitim tekrarı değildir.

| Akış | Yöntem | F3 örnek | F1 | F2 | F3 | F4 |
|---|---|---:|---:|---:|---:|---:|
| 240001 | A | 1024 | 0,156775 | 0,130200 | 0,475586 | 0,171500 |
| 240001 | A | 1536 | 0,156775 | 0,130200 | 0,432943 | 0,187500 |
| 240001 | replay | 1024 | 0,171450 | 0,168100 | 0,538086 | 0,173750 |
| 240001 | replay | 1536 | 0,171450 | 0,168100 | 0,545573 | 0,177500 |
| 240002 | A | 1024 | 0,163775 | 0,135900 | 0,483398 | 0,177750 |
| 240002 | A | 1536 | 0,163775 | 0,135900 | 0,421875 | 0,193500 |
| 240002 | replay | 1024 | 0,176050 | 0,178000 | 0,537109 | 0,177000 |
| 240002 | replay | 1536 | 0,176050 | 0,178000 | 0,543620 | 0,186000 |
| 240003 | A | 1024 | 0,159200 | 0,129600 | 0,454102 | 0,179750 |
| 240003 | A | 1536 | 0,159200 | 0,129600 | 0,406901 | 0,191250 |
| 240003 | replay | 1024 | 0,167725 | 0,173600 | 0,551758 | 0,182000 |
| 240003 | replay | 1536 | 0,167725 | 0,173600 | 0,542969 | 0,183500 |

## Bütçe ve eşleştirme

- Faz 1/2/4: 40.000 / 10.000 / 4.000 örnek; 2.500 / 625 / 250 güncelleme.
- Faz 3: 1.024 / 1.536 örnek; 64 / 96 güncelleme.
- Tam yol: 55.024 / 55.536 yeni örnek; 3.439 / 3.471 güncelleme.
- D480 penceresi 480 örnek ve 30 güncelleme; faz 4'ün %12'sidir.
- Replay faz 3'te tekrarlar dahil 9.216 / 13.824 örnek işler; A yalnızca
  1.024 / 1.536 örnek işler. Eşit adım sayısı eşit hesaplama değildir.
- Her yöntem/akış çifti faz 2 sonunda model, optimizer, tampon ve RNG
  durumundan iki adaya dallandı. Ortak 1.024 tahmin birebir eşleşti;
  kaynak faz-2 durumu değişmedi.
- Jeneratör 1000 ve başlangıç tohumu 7 sabit, üç akış tohumu farklıdır.
  Koşular arasında tüm rastgelelik kaynaklarının bağımsız olduğu iddia edilmez.

## Yorum: çift ölçüm gerekli

Seçilen 1.024 adayında A'nın F3–R2 doğruluğu %63,060–%64,445,
F4–R1 doğruluğu %86,380–%87,225'tir.
Replay'de bunlar sırasıyla %43,020–%44,145 ve %80,905–%82,050'dir.
Replay kendi önceki R1 performansından daha az kaybetti, fakat yeni kurala
uyumu da daha sınırlı kaldı. Düşük D480 tek başına üstünlük değildir;
faz2 referans düzeyleri yöntemler arasında farklıdır.

Hat 2 için yeni-kural öğrenimi ve eski-kural performansı birlikte raporlama
zorunluluğu [protokole](PROTOCOL.md) kaydedildi. Bu iki eksen tek bir
kazanan puanına indirgenmedi. Henüz mekanizma veya nedensel ayrıştırma
deneyi yapılmadı.

1.024 için önceden belirtilen 16–20 puan hasar öngörüsü gerçekleşmedi:
24,870–28,500 puan ölçüldü. 1.536 için 28–32 puan öngörüsünün de üzerinde,
32,970–35,890 puan gözlendi. Öngörüler seçim kuralı değildi;
20–40 puan bandı ve en kısa uygun aday kuralı aynen uygulandı.

64 güncellemelik R2 evresi, mekanizmaların tepki vermesi için sınırlı
bir bütçedir. Ayrı kontrollerde sabitlenen hiperparametrelerle tepkisizlik
olası sonuç olarak korunur; bu pilot böyle mekanizmaları sınamadı.

## Doğrulama ve kapsam

9 yeni karar testi ve 8 ortak çekirdek testi, toplam **17 ilgili test geçti**.
Tüm eski test paketi bu turda yeniden çalıştırılmadı.
12 aday satırında kayıt yükleme kontrolleri; altı yöntem/akış çiftinde
kaynak durum değişmezliği ve ortak önek tahmin eşitliği sağlandı.
Girdiler, gizli örnekler, hedefler, tahminler, kontrol noktaları ve koşu
öncesi kaynak/protokol kopyaları [manifest](results/manifest.json) ile saklandı.

**Öğrenilebilirlik kapısı hâlâ geçilmedi. Seçim yalnızca v0.3 pilotuna
aittir. Hat 2, v0.4, 1.792/768 adayları ve yeni mekanizmalar çalıştırılmadı.**
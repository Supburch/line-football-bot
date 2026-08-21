# Changelog

บันทึกการอัปเดตของ Line Football Bot — เรียงจากล่าสุดไปเก่า

## 2026-08-21 — ส่งภาพ Dome FC แบบรายภาพ (self-healing) + กัน cleanup ลบ key

### เปลี่ยนแปลง
- ปรับ `app/jobs/dome_fc.py` ให้ติดตามการส่งแบบ **รายภาพ** (`dome_fc_image_<index>`) แทนรายวัน (`dome_fc_greeting_<date>`) — ภาพไหนยังไม่ส่งจะถูกตามส่งในรันถัดไปอัตโนมัติ (self-healing)
- ขยายวันสุดท้ายแคมเปญเป็น **23 ส.ค.** (+2 วัน grace สำหรับ catch-up)

### แก้ไข
- แก้ `cleanup_sent_events_db()` ใน `app/repositories/supabase_client.py` ไม่ให้ลบ key ที่ขึ้นต้นด้วย `dome_fc_image_%` (เดิม cleanup ทุก 24 ชม. ลบ key เหล่านี้ ทำให้ภาพถูกส่งซ้ำทั้งหมด)


## 2026-08-20 — แคมเปญ Dome FC ปิดฉาก (วันสุดท้าย 21 ส.ค.)

### เพิ่ม
- ส่งภาพ Dome FC ใบที่ **19** และ **20** พร้อมกันในวันสุดท้ายของแคมเปญ (21 ส.ค.)
- ข้อความพิเศษต้อนรับพรีเมียร์ลีกในวันสุดท้าย ต่อท้ายคำทักทายตอนเช้า:
  > ⚽🔥 พรีเมียร์ลีกกลับมาแล้ว! เตรียมมันส์ครบทุกแมตช์ เริ่มวันนี้

### เปลี่ยนแปลง
- ปรับโครงสร้าง `app/jobs/dome_fc.py` ให้รองรับการส่งหลายภาพต่อวันผ่าน helper `_day_indices_for(today_date)`
- หลัง 21 ส.ค. โค้ดคืนค่าลิสต์ว่าง = ไม่มีการ์ด Dome FC อีกต่อไป (ปิดแคมเปญ)

### แก้ไข
- ฟื้นฟูการส่งภาพ Dome FC ในคำทักทายตอนเช้าที่หายไป (BASE_URL normalization)

### Commits
- `a1c5720` feat: add premier league kickoff message on final dome fc day
- `54c4f01` feat: send dome fc images 19 and 20 together on final day
- `7f4c554` fix: restore Dome FC image in morning greeting

## 2026-08-19
- `d019cc1` feat: extend dome fc greeting to aug 21 to retry missed image
- `8b72079` fix: force https for image urls, handle broadcast timeout, and fix test assertions

## 2026-08-18
- `a01b3ad` fix: multiple critical and minor bugs, update help text

## 2026-08-12
- `11a9f86` feat: switch goal notifications to silent tracking and add red card alerts

## 2026-07-29
- `8054be2` feat: add Dome FC morning greeting images and job

## 2026-07-06
- `5bcc925` fix: limit startup greeting check to 08:00-09:59 BKK window only
- `213cf70` Update morning greeting to show only greeting and top scorers

## 2026-07-01
- `fa62d6f` feat: disable live score alerts for WC 26 (LIVE_SCORE_WC_DISABLED=True)

## 2026-06-29
- `97a5c07` Update free TV schedule for Round of 32 (ThairathSport)

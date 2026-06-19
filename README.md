# Barcode API

Self-hosted HTTP API для генерации штрихкодов и GS1 DataMatrix.

Поддерживаемые типы:

* EAN-13
* EAN-8
* QR Code
* GS1 DataMatrix (Честный Знак, GS1)

---

## Health Check

### Request

```http
GET /health
```

### Response

```json
{
  "ok": true
}
```

---

# Generate Barcode

### Request

```http
GET /barcode.png
```

### Query Parameters

| Parameter | Required | Description                       |
| --------- | -------- | --------------------------------- |
| type      | yes      | Barcode type                      |
| data      | yes      | Data to encode                    |
| w         | no       | Output image width (default 150)  |
| h         | no       | Output image height (default 150) |

### Response

```http
200 OK
Content-Type: image/png
```

---

# EAN-13

### Example

```http
GET /barcode.png?type=ean13&data=4601234567893
```

### cURL

```bash
curl -o ean13.png \
"http://localhost:8000/barcode.png?type=ean13&data=4601234567893"
```

Requirements:

* exactly 13 digits

---

# EAN-8

### Example

```http
GET /barcode.png?type=ean8&data=96385074
```

### cURL

```bash
curl -o ean8.png \
"http://localhost:8000/barcode.png?type=ean8&data=96385074"
```

Requirements:

* exactly 8 digits

---

# QR Code

### Example

```http
GET /barcode.png?type=qr&data=Hello%20World
```

### cURL

```bash
curl -o qr.png \
"http://localhost:8000/barcode.png?type=qr&data=Hello%20World"
```

Requirements:

* arbitrary UTF-8 string

---

# GS1 DataMatrix

Supports:

* GS1 marks from Честный Знак
* GS separators
* AI 01
* AI 21
* AI 91
* AI 92
* AI 93

### Example (raw GS separator)

```
010465044027571921K6Y7AM5UICAK4<GS>91IZCC<GS>92WI+.1SIODKC/5_FE2G=69O229Z9XC.S_UHE1YR:PO+CN
```

### URL Encoded Example

```http
GET /barcode.png?type=gs1-dm&data=010465044027571921K6Y7AM5UICAK4%1D91IZCC%1D92WI%2B.1SIODKC%2F5_FE2G%3D69O229Z9XC.S_UHE1YR%3APO%2BCN
```

### cURL

```bash
curl -o mark.png \
"http://localhost:8000/barcode.png?type=gs1-dm&data=010465044027571921K6Y7AM5UICAK4%1D91IZCC%1D92WI%2B.1SIODKC%2F5_FE2G%3D69O229Z9XC.S_UHE1YR%3APO%2BCN"
```

---

# Supported GS Formats

The API automatically recognizes:

### JSON GS

```text
\u001D
```

### Escape Sequence

```text
\x1D
```

### URL Encoded GS

```text
%1D
```

### Placeholder

```text
<GS>
```

### TEC-IT Style Prefix

```text
\F0104603400000029211AzZK?b\x1D93R=92
```

---

# Image Size

Default:

```text
150x150
```

Custom size:

```http
GET /barcode.png?type=gs1-dm&data=...&w=300&h=300
```

---

# Google Sheets

## EAN-13

```excel
=IMAGE("https://barcode.example.com/barcode.png?type=ean13&data=" & ENCODEURL(A2) & "&w=150&h=60";4;60;150)
```

## EAN-8

```excel
=IMAGE("https://barcode.example.com/barcode.png?type=ean8&data=" & ENCODEURL(A2) & "&w=150&h=60";4;60;150)
```

## GS1 DataMatrix

```excel
=IMAGE("https://barcode.example.com/barcode.png?type=gs1-dm&data=" & ENCODEURL(F2) & "&w=150&h=150";4;150;150)
```

## QR Code

```excel
=IMAGE("https://barcode.example.com/barcode.png?type=qr&data=" & ENCODEURL(A2) & "&w=150&h=150";4;150;150)
```

---

# Error Codes

## 400 Bad Request

Invalid request parameters.

Example:

```json
{
  "detail": "EAN-13 must be exactly 13 digits"
}
```

## 422 Unprocessable Entity

Barcode generation failed.

Example:

```json
{
  "detail": "zint failed"
}
```

## 500 Internal Server Error

Unexpected server error.

---

# Cache

Responses include:

```http
Cache-Control: public,max-age=86400
```

allowing browsers and Google Sheets to cache generated images for 24 hours.

def jq_transform() -> str:
    return r"""
.[] | {
  gid: "00000000-0000-0000-0000-000000000000",
  gid_url: ("https://bonus.is/product/" + (.ItemNo | tostring)),
  label: .Description2,
  content: [
    {
      "type": "Description",
      "value": .Description
    }
  ],
  metrics: {
    "unit_price_including_vat": .UnitPriceIncludingVAT | (try tonumber catch 0.0),
    "unit_price_excluding_vat": .UnitPriceExcludingVAT | (try tonumber catch 0.0),
    "vat_percentage": .VATPCT | (try tonumber catch 0.0),
    "quantity_box": .QtyKassi | (try tonumber catch 0.0)
  },
  flags: {
    "in_pottur": .inPottur,
    "is_active": (if .isActive == "VIRK" then true elif .isActive == "ÓVIRK" then false else null end)
  },
  dimensions: {
    "item_category_code": .ItemCategoryCode | tostring,
    "product_group_code": .ProductGroupCode | tostring,
  },
  properties: {
    "vendor_item_no": .VendorItemNo | tostring,
    "purchase_uom": .PurchaseUOM | tostring,
    "date_created": .DateCreated | tostring
  },
  ids: [
    {
      "id": .Barcode,
      "role": "self",
      "label": "barcode"
    },
    {
      "id": .VendorItemNo,
      "role": "self",
      "label": "vendor_item_no"
    },
    {
      "id": .VendorNo,
      "role": "self",
      "label": "vendor_no"
    },
    {
      "id": .OriginalVendorNo,
      "role": "self",
      "label": "original_vendor_no"
    },
    {
      "id": .OriginalVendorItemNo,
      "role": "self",
      "label": "original_vendor_item_no"
    }
  ],
  "partition": "bonus.is",
  "sign": 1
}
"""
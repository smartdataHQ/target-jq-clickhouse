def jq_transform() -> str:
    return r"""
(if type=="array" then . else [.] end)
| map(
  . as $r
  | ($r.salesInvoiceLines? // null)    as $sil
  | ($r.purchaseInvoiceLines? // null) as $pil
  | (( $sil | type ) == "array")       as $is_sales
  | (( $pil | type ) == "array")       as $is_purchase
  | ( $sil // $pil // [] )             as $lines

  | {
      entity_gid: ($r.company_id | tostring),
      type: ("track" | tostring),
      event: (if $is_sales then "sales_invoices" else "purchase_invoices" end),
      timestamp: ($r.invoiceDate),

      location: (
        if $is_sales then
          [
            {
              "location_of": "shipping_address",
              "label": $r.shipToName,
              "street": ($r.sellToAddressLine1 // "" | tostring),
              "region": ($r.sellToCity // "" | tostring),
              "postal_code": ($r.sellToPostCode // "" | tostring),
              "country": ($r.sellToCountry // "" | tostring),
              "longitude": (($r.shipping_address__longitude // 0) | tonumber),
              "latitude":  (($r.shipping_address__latitude  // 0) | tonumber)
            },
            {
              "location_of": "billing_address",
              "label": $r.billToName,
              "street": ($r.billToAddressLine1 // "" | tostring),
              "region": ($r.billToCity // "" | tostring),
              "postal_code": ($r.billToPostCode // "" | tostring),
              "country": ($r.billToCountry // "" | tostring),
              "longitude": (($r.billing_address__longitude // 0) | tonumber),
              "latitude":  (($r.billing_address__latitude  // 0) | tonumber)
            }
          ]
        else
          [
            {
              "location_of": "shipping_address",
              "label": $r.shipToName,
              "street": ($r.shipToAddressLine1 // "" | tostring),
              "region": ($r.shipToCity // "" | tostring),
              "postal_code": ($r.shipToPostCode // "" | tostring),
              "country": ($r.shipToCountry // "" | tostring),
              "longitude": (0 | tonumber),
              "latitude":  (0 | tonumber)
            },
            {
              "location_of": "billing_address",
              "label": $r.payToName,
              "street": ($r.payToAddressLine1 // "" | tostring),
              "region": ($r.payToCity // "" | tostring),
              "postal_code": ($r.payToPostCode // "" | tostring),
              "country": ($r.payToCountry // "" | tostring),
              "longitude": (0 | tonumber),
              "latitude":  (0 | tonumber)
            }
          ]
        end
      ),

      "traits.id":   (( $r.customerId // $r.vendorId // "" ) | tostring),
      "traits.name": (if $is_sales
                        then ((($r.customerName // "") + " " + ($r.customer__last_name // "")) | tostring)
                        else ($r.vendorName // "" | tostring)
                      end),
      "traits.email": ($r.email // "" | tostring),
      "traits.phone": ($r.phoneNumber // "" | tostring),

      properties: ({    
        invoice_number: ($r.number // "" | tostring)
      }),

      dimensions: {
        status: ($r.status // "" | tostring)
      },
     
      metrics: {
        remaining_amount: (($r.remainingAmount // 0) | tonumber)
      },

      flags: ({
        prices_include_tax: ($r.pricesIncludeTax // false),
        discount_applied_before_tax: ($r.discountAppliedBeforeTax // false)
      }),

      "commerce.checkout_id": ($r.paymentTermsId // $r.orderId // "" | tostring),
      "commerce.revenue":     (($r.totalAmountExcludingTax // 0) | tonumber),
      "commerce.tax":         (($r.totalTaxAmount         // 0) | tonumber),
      "commerce.discount":    (($r.discountAmount         // 0) | tonumber),
      "commerce.currency":    ($r.currencyCode            // "" | tostring),

      "commerce.products": (
        $lines
        | map({
            line_id: (.id | tostring),
            product_id: (.itemId | tostring),
            product: (.description // "" | tostring),
            units: ((.quantity // 0) | tonumber),

            # Prefer unitCost when present (purchase); otherwise compute from amounts (sales)
            unit_price: (
              if has("unitCost") and ((.unitCost // 0) | tonumber) > 0 then
                ((.unitCost // 0) | tonumber)
              elif ((.quantity // 0) | tonumber) != 0 then
                ((.amountExcludingTax // 0) | tonumber) / ((.quantity // 1) | tonumber)
              else 0 end
            ),
            unit_cost: (
              if has("unitCost") then
                ((.unitCost // 0) | tonumber)
              elif ((.quantity // 0) | tonumber) != 0 then
                ((.amountIncludingTax // 0) | tonumber) / ((.quantity // 1) | tonumber)
              else 0 end
            ),

            uom: (.unitOfMeasureCode // "" | tostring),
            tax_percentage: ((.taxPercent // 0) | tonumber),
            discount_percentage: ((.discountPercent // 0) | tonumber)
          })
      ),

      event_gid: ($r.id | tostring),
      partition: (($r.company_name // "" | ascii_downcase | gsub("\\s+"; "."))),
      sign: 1
    }
)
"""
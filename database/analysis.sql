CREATE OR REPLACE VIEW v_crop_price_comparison AS
SELECT c.id AS crop_id, c.name AS crop_name,
       p.price AS farmer_price, w.price AS wholesaler_price, r.price AS retailer_price
FROM CROP AS c
LEFT JOIN (
    SELECT crop_id, MIN(discounted_price) AS price
    FROM v_production_pricing
    WHERE quantity_kg > 0 AND expiry_date >= CURDATE()
    GROUP BY crop_id
) AS p ON p.crop_id = c.id
LEFT JOIN (
    SELECT crop_id, MIN(discounted_price) AS price
    FROM v_wholesaler_stock_pricing
    WHERE quantity_kg > 0 AND expiry_date >= CURDATE()
    GROUP BY crop_id
) AS w ON w.crop_id = c.id
LEFT JOIN (
    SELECT crop_id, MIN(discounted_price) AS price
    FROM v_retail_stock_status
    WHERE quantity_kg > 0 AND expiry_date >= CURDATE()
    GROUP BY crop_id
) AS r ON r.crop_id = c.id;

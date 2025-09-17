<?php

// Function to make cURL request
function makeApiRequest($endpoint, $params = []) {
    $baseUrl = 'https://clan.com/clan/api';
    //$baseUrl = 'https://bast-clan.hotcheck.co.uk/clan/api';
    $url = $baseUrl . $endpoint;

    // Build query string if parameters exist
    if (!empty($params)) {
        $url .= '?' . http_build_query($params);
    }

    // Initialize cURL session
    $ch = curl_init($url);

    // Set cURL options
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array(
        'Content-Type: application/json',
        // Add authorization header if required
        // 'Authorization: Bearer your_access_token'
    ));

    // Execute cURL request
    $response = curl_exec($ch);

    // Check for cURL errors
    if (curl_errno($ch)) {
        $result = [
            'success' => false,
            'message' => 'cURL error: ' . curl_error($ch)
        ];
    } else {
        // Debug: Show raw response
        echo "Raw response: " . substr($response, 0, 500) . "...\n";
        
        // Decode JSON response
        $result = json_decode($response, true);

        // Check if JSON decoding was successful
        if (json_last_error() !== JSON_ERROR_NONE) {
            $result = [
                'success' => false,
                'message' => 'JSON decoding error: ' . json_last_error_msg(),
                'raw_response' => substr($response, 0, 200)
            ];
        }
    }

    // Close cURL session
    curl_close($ch);

    return $result;
}

// Function to get single product data
function getProductData($sku, $all_images = false, $include_categories = false) {
    $params = [
        'sku' => $sku,
        'all_images' => $all_images ? 1 : 0,
        'include_categories' => $include_categories ? 1 : 0
    ];

    return makeApiRequest('/getProductData', $params);
}

// Function to get multiple products
function getProducts($limit = null) {
    $params = [];
    if ($limit !== null) {
        $params['limit'] = $limit;
    }

    return makeApiRequest('/getProducts', $params);
}

function getCategoryTree() {
    $params = [];
    return makeApiRequest('/getCategoryTree', $params);
}

// Example usage
try {
    // Example: Get multiple products with limit
    $productsData = getProducts(limit: 10);

    // Output products list
    echo "Products List:\n";
    echo json_encode($productsData, JSON_PRETTY_PRINT) . "\n";

    // Example: Get single product data
    /*
    $productData = getProductData(
        sku: 'sr_swhdr_eightyardkilt_flashes',
        all_images: false,
        include_categories: false
    );
    // Output single product data
    echo "Single Product Data:\n";
    echo json_encode($productData, JSON_PRETTY_PRINT) . "\n\n";
    */

    // Example get category tree
    $catTree = getCategoryTree();

    echo "Categories:\n";
    echo json_encode($catTree, JSON_PRETTY_PRINT) . "\n\n";

} catch (Exception $e) {
    echo json_encode([
        'success' => false,
        'message' => 'Error: ' . $e->getMessage()
    ], JSON_PRETTY_PRINT);
}

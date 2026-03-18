<?php

function callApi($api_function, $args = [], $files = []) {
    $url = 'https://clan.com/clan/blog_api/' . $api_function;

    $params['api_user'] = 'blog';
    $params['api_key'] = 'AC%7ef2a5A!24bd*E844a83f9F$49a02';
    //$url = 'https://bast-clan.hotcheck.co.uk/clan/blog_api/' . $api_function;
    //$params['api_key'] = '83f9F$49a02AC%7ef2a5A!24bd*E844a';

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);

    // Handle file uploads if provided
    if (!empty($files)) {
        foreach ($files as $key => $filePath) {
            if (file_exists($filePath)) {
                $params[$key] = new CURLFile($filePath);
            } else {
                throw new ErrorException("File not found: " . $filePath);
            }
        }
    }

    $params['json_args'] = json_encode($args);
    //var_dump($params);

    curl_setopt($ch, CURLOPT_POSTFIELDS, $params);
    $response = curl_exec($ch);

    if (curl_errno($ch)) {
        $error = curl_error($ch);
        curl_close($ch);
        return $error;
    }

    curl_close($ch);
    //return json_decode($response, true);
    return $response;
}

// GET POST(S)
// provide a psot id for all data for a post
// or leave blank for a list of post_id => title
//$response = callApi('getPosts');
//$response = callApi('getPosts', ['post_id' => 123]);

// GET IMAGES
// images in path /media/blog/
// $response = callApi('getImages');

// UPLOAD IMAGE
// $response = callApi('uploadImage', [], ['test-image2.jpg']); // file path relative to script

// CREATE POST
$response = callApi('createPost', [
        'title' => 'api test post', // required
        'url_key' => 'test-post-10',  // required
        'short_content' => 'The identity—and later, a global fashion statement—mirrors Scotland’s own turbulent and triumphant narrative. This expanded exploration delves deeper into the kilt’s  <strong> short blurb</strong> that will be shown on the blog listing.', 
        'status' => 2, // enabled 
        'categories' => [9, 17],
        'list_thumbnail' => '/blog/test-image.jpg', // path from /media e.g. /blog/someimage.jpg
        'post_thumbnail' => '/blog/test-image.jpg', // path from /media e.g. /blog/someimage.jpg
        'meta_title' => 'Meta title test', 
        'meta_tags' => 'meta,tags,test', 
        'meta_description' => 'Meta description test', 
    ], ['html_file' => 'new_test.html']); // file path relative to script (key html_file required)

// EDIT POST
// only provide fields you want to change
/*
$response = callApi('editPost', [
    'post_id' => 333, // id of post to change
], ['html_file' => 'your_post.html']);
*/

// Response will be json string
//echo $response . "\n\n";
// Pretty print response
echo json_encode(json_decode($response, true), JSON_PRETTY_PRINT) . "\n";






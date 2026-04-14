$( document ).ready(function() {



  // selector cache
  var
    $showoriginal  = $('.menuoption#showoriginal'),
    $showmodified  = $('.menuoption#showmodified'),
    $showidentical = $('.menuoption#showidentical'),
    $codeprintmargin  = $('.menuoption#codeprintmargin'),
    $highlight  = $('.menuoption#highlight'),
    $dosyntaxhighlight  = $('.menuoption#dosyntaxhighlight');

  $showoriginal.state = true
  $showoriginal.on("click", function(){
    switch ($showoriginal.state) {
    case false:
       $('#leftcode').show()
       $('.right_diff_del').show()
       $('.lineno_rightdel').show()
       $showoriginal.state = true
        break;
    case true:
       $('#leftcode').hide()
       $('.right_diff_del').hide()
       $('.lineno_rightdel').hide()
       $showoriginal.state = false
        break;
      }
  });

  $showmodified.state = true
  $showmodified.on("click", function(){
    switch ($showmodified.state) {
    case false:
       $('#rightcode').show()
       $('.left_diff_add').show()
       $('.lineno_leftadd').show()
       $showmodified.state = true
        break;
    case true:
       $('#rightcode').hide()
       $('.left_diff_add').hide()
       $('.lineno_leftadd').hide()
       $showmodified.state = false
        break;
      }
  });

  $showidentical.state = true
  $showidentical.on("click", function(){
    switch ($showidentical.state) {
    case false:
       $('.lineno_requ_q').show()
       $('.lineno_rightchange_q').show()
       $('.lineno_rightdel_q').show()
       $('.lineno_rightadd_q').show()
       $('.right_identical').show()
       $('.lineno_lequ_q').show()
       $('.lineno_leftchange_q').show()
       $('.lineno_leftdel_q').show()
       $('.lineno_leftadd_q').show()
       $('.left_identical').show()
       $showidentical.state = true
        break;
    case true:
       $('.lineno_requ_q').hide()
       $('.lineno_rightchange_q').show()
       $('.lineno_rightdel_q').show()
       $('.lineno_rightadd_q').show()
       $('.right_identical').hide()
       $('.lineno_lequ_q').hide()
       $('.lineno_leftchange_q').show()
       $('.lineno_leftdel_q').show()
       $('.lineno_leftadd_q').show()
       $('.left_identical').hide()
       $showidentical.state = false
        break;
      }
  });

  $codeprintmargin.state = true
  $codeprintmargin.on("click", function(){
    switch ($codeprintmargin.state) {
    case false:
       $('.printmargin').show()
       $codeprintmargin.state = true
        break;
    case true:
       $('.printmargin').hide()
       $codeprintmargin.state = false
        break;
      }
  });


  $highlight.state = true
  $highlight.on("click", function(){
    switch ($highlight.state) {
    case false:
       $('.left_diff_change').removeClass('clearbg');
       $('.left_diff_del').removeClass('clearbg');

       $('.right_diff_add').removeClass('clearbg');
       $('.right_diff_change').removeClass('clearbg');
       $highlight.state = true
        break;
    case true:
       $('.left_diff_change').addClass('clearbg');
       $('.left_diff_del').addClass('clearbg');

       $('.right_diff_add').addClass('clearbg');
       $('.right_diff_change').addClass('clearbg');
       $highlight.state = false
        break;
      }
  });

  var originalStyle = $("link.syntaxdef").attr("href")
  var bwStyle = originalStyle.slice(0,originalStyle.lastIndexOf('/'))+'/bw.css'
  $dosyntaxhighlight.state = true
  $dosyntaxhighlight.on("click", function(){
    switch ($dosyntaxhighlight.state) {
    case false:
       $("link.syntaxdef").attr("href", originalStyle);
       $dosyntaxhighlight.state = true
        break;
    case true:
       $("link.syntaxdef").attr("href", bwStyle);
       $dosyntaxhighlight.state = false
        break;
      }
  });


});
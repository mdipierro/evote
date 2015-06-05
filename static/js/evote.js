jQuery(function(){
        var uls=[];
        jQuery('.model-ranking').attr('readonly',true).each(function(){var ul=jQuery(this).closest('ul'); ul.find('li').addClass('ranking-option').find('input').addClass('hidden'); if(uls.indexOf(ul)<0) uls.push(ul); }); 
        
        for(var k=0;k<uls.length;k++) uls[k].sortable({onDrop:function(a,b,c,d){jQuery(b).find('input.model-ranking').each(function(i){jQuery(this).val(i+1);});c(a,b);}});

    });

function get_random() {
    var d = new Date().getTime();
    var uu8 = 'xxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = (d + Math.random()*16)%16 | 0;
            d = Math.floor(d/16);
            return r;
        });
    return uu8;
};

let NEW_QUESTION = {'preamble':'', 'answers':['','',''], 'algorithm':'simple-majority', 
                    'randomize':true, 'comments':false, 'name': null};
                    
let ALGORITHMS = ['simple-majority'] // ,'instant-runoff','borda','schulze'];
let app = {}; 
let init = (app) => {
    app.data = {
        questions: [],
        algorithms: ALGORITHMS 
    };
    app.methods = {
        delete_question: function(q) {
            app.vue.questions.splice(q,1);
        },
        delete_answer: function(q, a) {
            app.vue.questions[q].answers.splice(a,1);
        },
        append_question: function() {
            var question = JSON.parse(JSON.stringify(NEW_QUESTION));
            question.name = get_random();
            app.vue.questions.push(question);
        },
        append_answer: function(q) {
            app.vue.questions[q].answers.push('');
        }
    };
    app.filters = {
    };
    app.init = () => {        
        app.vue = new Vue({el: '#target-ballot',
                           data: app.data, 
                           methods: app.methods, 
                           filters:app.filters});    
        
        try {
            app.vue.questions = JSON.parse(jQuery('#election_ballot_model').val());
        } catch(e) {}
    };
    app.init();
};    

init(app);
jQuery('form').submit(function(){
        jQuery('#election_ballot_model').val(JSON.stringify(app.vue.questions));
    });

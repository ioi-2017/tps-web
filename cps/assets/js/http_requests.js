/**
 * Source: https://gist.github.com/JeffreyWay/5112282
 * Adapted to Django by Amir Keivan Mohtashami <akmohtashami97@gmail.com>
 * Requires JQuery and Javascript Cookie Library(https://github.com/js-cookie/js-cookie/)
 */

(function() {

  var requests = {
    initialize: function() {
      this.methodLinks = $('a[data-method]');

      this.registerEvents();
    },

    registerEvents: function() {
      this.methodLinks.on('click', this.handleMethod);
    },

    handleMethod: function(e) {
      var link = $(this);
      var httpMethod = link.data('method').toUpperCase();
      var form;

      // If the data-method attribute is not PUT or DELETE,
      // then we don't know what to do. Just ignore.
      if ( $.inArray(httpMethod, ['PUT', 'DELETE']) === - 1 ) {
        return;
      }

      // Allow user to optionally provide data-confirm="Are you sure?"
      if ( link.data('confirm') ) {
        if ( ! requests.verifyConfirm(link) ) {
          return false;
        }
      }

      form = requests.createForm(link);
      form.submit();

      e.preventDefault();
    },

    verifyConfirm: function(link) {
      return confirm(link.data('confirm'));
    },

    createForm: function(link) {
      var form =
      $('<form>', {
        'method': 'POST',
        'action': link.attr('href')
      });

      var token =
      $('<input>', {
        'type': 'hidden',
        'name': 'csrfmiddlewaretoken',
        'value': Cookies.get('csrftoken')
      });


      var hiddenInput =
      $('<input>', {
        'name': '_method',
        'type': 'hidden',
        'value': link.data('method')
      });

      return form.append(token, hiddenInput)
                 .appendTo('body');
    }
  };

  requests.initialize();

})();
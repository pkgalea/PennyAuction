
$(document).ready(function(){
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
    var numbers_received = [];

    //receive details from server
    socket.on('newnumber', function(msg) {
        console.log("Received number" + msg.upcoming);
  
        $('#log').html(msg.upcoming);
        $('#auction0').html(msg.auction0)
        $('#auction1').html(msg.auction1)
        $('#auction2').html(msg.auction2)
        $('#auction3').html(msg.auction3)
        $('#auction4').html(msg.auction4)
        $('#auction5').html(msg.auction5)
        $('#auction6').html(msg.auction6)
        $('#auction7').html(msg.auction7)
        $('#auction8').html(msg.auction8)
        $('#auction9').html(msg.auction9)
       }
    
    
    );

});
Date.prototype.addDays = function(days) {
	this.setDate(this.getDate()+days);
}
function cambiaDias() {
	dias = parseInt($('#id_dias').val());
	hasta = new Date();
	hasta.addDays(dias);
	$('#id_hasta').text(hasta.toLocaleDateString());
}
$(document).ready(function(){
	$('#id_dias').change(cambiaDias);
	
	$('form').validate({
		rules: {
			dias: {
				required:true,
				number:true,
				min:1,
			},
		},
		messages: {
			dias: {
				required:"Debe ingresar la cantidad de dias para los cuales desea crear turnos",
				number:"Debe ingresar un número entero positivo",
				min:"Debe ingresar un número mayor a cero",
			},
		}
	});
});
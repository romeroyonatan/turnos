$.validator.addMethod("passwd", function(value) {
   return value.length >= 6 && // logitud minima
   		  /[a-z]/.test(value) &&// tiene una letra minuscula
   		  /\d/.test(value) // tiene un digito
}, "La password debe contener 6 caracteres y al menos una letra minúscula y un número");

$(document).ready(function(){
	$('form').validate({
		rules: {
			first_name:{
				required:true,
			},
			last_name:{
				required:true,
			},
			email:{
				required:true,
				email:true,
			},
			username:{
				required:true,
				max_length:30,
			},
			password1:{
				passwd:true,
				required:true,
			},
			password2:{
				equalTo:"#id_password1"
			},
			dni: {
				required:true,
				number:true,
			},
		},
		messages: {
			dias: {
				required:"Debe ingresar la cantidad de dias para los cuales desea crear turnos",
				number:"Debe ingresar un número entero positivo",
			},
		}
	});
});
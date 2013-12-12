String.prototype.format = function () {
    var literal = this;
    for (var i = 0; i < arguments.length; i++) {
        var regex = new RegExp('\\{' + i + '\\}', 'g');
        literal = literal.replace(regex, arguments[i]);
    }
    return literal;
};
/**
 * Devuelve el numero con 2 digitos significativos
 */
function n(n){
    return n > 9 ? n: "0" + n;
}
$(document).ready(function(){
	$("#id_dni").blur(function() {
		dni = $("#id_dni").val();
		// TODO Validacion DNI
		if(dni) {
			url = '/json/afiliado/dni/{0}/'.format(dni);
			$.getJSON(url, function(data) {
				// TODO Caso DNI Inexistente
				if(data.length > 0) {
					//TODO Caso DNI Duplicado
					if (data.length > 1)
						console.log('DNI Duplicado');
					
					$("#id_afiliado").val(data[0].id);
					$("#id_numero").val(data[0].numero);
					$("#id_nombre").val(data[0].nombre);
					$("#id_apellido").val(data[0].apellido);
					
					// Verificar telefono
					url = '/json/afiliado/id/{0}/telefono/'.format(data[0].id);
					$.getJSON(url, function(data) {
						$("#id_telefono").val(data[0].telefono);
					});
					//TODO Verificar presentismo
				}
			});
		}
	});
	
	defaultMessage = "Seleccionar"
	dia=["Domingo", "Lunes", "Martes", "Miercoles", "Jueves","Viernes","Sabado"]
	mes=["enero", "febrero","marzo", "abril","mayo", "junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
		
	$("#id_especialidad").change(function() {
		$("#id_especialista, #id_dia, #id_hora").prop({disabled: true});
		var id = $("#id_especialidad").val();
		if(!id)
			return;
		var url = '/json/especialistas/especialidad/{0}/'.format(id);
		var destino = $('#id_especialista');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,defaultMessage);
				$.each(data,function(index, value){
					options += '<option value="{0}">{1} {2}</option>'.format(value.id,
																			 value.apellido,
																			 value.nombre);
				});
				destino.empty().append(options);
			}
		});
	});
	
	
	$("#id_especialista").change(function() {
		$("#id_dia, #id_hora").prop({disabled: true});
		var id = $("#id_especialista").val();
		if(!id)
			return;
		var url = '/json/turnos/{0}/'.format(id);
		var destino = $('#id_dia');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,defaultMessage);
				$.each(data,function(index, value){
					var milis = value.fecha * 1000;
					var fecha = new Date(milis)
					options += '<option value="{0}">{1}, {2} de {3}</option>'.format(milis, 
																					 dia[fecha.getDay()],
																					 fecha.getDate(),
																					 mes[fecha.getMonth()]);
				});
				destino.empty().append(options);
			}
		});
	});
	
	
	$("#id_dia").change(function() {
		$("#id_hora").prop({disabled: true});
		var milis = parseInt($("#id_dia").val());
		var id = $("#id_especialidad").val();
		if(!id)
			return;
		var d = new Date(milis);
		var url = '/json/turnos/{0}/{1}/{2}/{3}/'.format(id, d.getFullYear(),d.getMonth()+1,d.getDate());
		var destino = $('#id_hora');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,defaultMessage);
				$.each(data,function(index, value){
					fecha = new Date(value.fecha * 1000)
					options += '<option value="{0}">{1}:{2}</option>'.format(value.id, 
																			 n(fecha.getHours()),
																			 n(fecha.getMinutes()));
				});
				destino.empty().append(options);
			}
		});
	});
	
	$("#id_agregar").click(function() {
		var id_turno = $("#id_hora").val();
		var id_afiliado = $("#id_afiliado").val();
		var id = $("#id_especialidad").val();
		if(!id)
			return;
		var d = new Date(milis);
		var url = '/json/turnos/{0}/{1}/{2}/{3}/'.format(id, d.getFullYear(),d.getMonth()+1,d.getDate());
		var destino = $('#id_hora');
		$.getJSON(url, function(data) {
			if(data.length > 0) {
				destino.removeAttr('disabled');
				var options = "<option value='{0}'>{1}</option>".format(0,defaultMessage);
				$.each(data,function(index, value){
					fecha = new Date(value.fecha * 1000)
					options += '<option value="{0}">{1}:{2}</option>'.format(value.id, 
																			 n(fecha.getHours()),
																			 n(fecha.getMinutes()));
				});
				destino.empty().append(options);
			}
		});
	});
	
});
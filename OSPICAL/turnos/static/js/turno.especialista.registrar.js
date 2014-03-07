var template = "<tr id='tr-{id}'><td>{especialidad}</td><td>{consultorio}" +
		"</td><td>{dia}</td><td>{desde} a {hasta}</td><td><a id='rem-tr-{id}' " +
		"class='boton_eliminar pure-u-1-5' href='#'><span class='ui-icon " +
		"ui-icon-closethick' title='Eliminar'></span></a></td></tr>"
registrar = {
	lista : null,
	add: function() {
		var disponibilidad = { 
				id: registrar.lista.length(),
				disponibilidad_id: null,
				especialidad_id: $('#id_especialidad').val(),
				especialidad: $('#id_especialidad :selected').text(),
				dia_id: $('#id_dia').val(),
				dia: $('#id_dia :selected').text(),
				desde: $('#id_desde').val(),
				hasta: $('#id_hasta').val(),
				consultorio: $('#id_consultorio').val(),
		};
		if(registrar.validate(disponibilidad, true))
			if(!registrar.lista.add(disponibilidad))
				mostrarMensaje(MESSAGE_ELEMENTO_EXISTENTE,
						       {title:MESSAGE_ELEMENTO_EXISTENTE_TITLE});
	},
	validate: function(object, showMessages) {
		if(showMessages != null && showMessages == true) {
			if(!object.especialidad_id) 
				mostrarMensaje(MESSAGE_ERROR_ESPECIALIDAD,
								{element:$('#id_especialidad')});
			else if(!object.consultorio)
				mostrarMensaje(MESSAGE_ERROR_CONSULTORIO,
								{element:$('#id_consultorio')});
			else if(!object.dia_id)
				mostrarMensaje(MESSAGE_ERROR_DIA,
								{element:$('#id_dia')});
			else if(!object.desde)
				mostrarMensaje(MESSAGE_ERROR_HORA_DESDE,
								{element:$('#id_desde')});
			else if(!object.hasta)
				mostrarMensaje(MESSAGE_ERROR_HORA_HASTA,
								{element:$('#id_hasta')});
		}
		return object.especialidad_id && object.consultorio && 
			   object.dia_id && object.desde && object.hasta;
	}
};
Lista.prototype.__push = function(obj) {
	this.objects.push(obj);
}
Lista.prototype.__exists = function(obj) {
	var exists = false;
	var i = 0;
	while (!exists && i < this.objects.length) {
		var object = this.objects[i];
		exists = (object.especialidad_id == obj.especialidad_id &&
				object.dia_id 		 	 ==	obj.dia_id &&
				object.desde 		 ==	obj.desde &&
				object.hasta 		 ==	obj.hasta);
		i++;
	} 
	return exists;
}
Lista.prototype.__rebuild = function(objects) {
	for(var i=0; i < objects.length; i++)
		this.addDOM(objects[i]);
}
Lista.prototype.__validate = function(object) {
	return registrar.validate(object);
}

$(document).ready(function(){
	registrar.lista = new Lista($('#id_disponibilidades'),
			{listContainer: $('#table_disponibilidades > tbody'),
			template:template}),
	$('#id_dni').number(true, 0,',','.');
	$('#id_agregar').click(registrar.add);
	$('#id_desde, #id_hasta').timepicker({ 'step':15,
								'scrollDefaultNow': true,
								'timeFormat':'G:i'
							 });
	$('form').submit(function() {
		$('#id_dni').number(true,0,'','');
	});
	$('form').validate({
		rules: {
			dni:{
				required:true,
			},
			nombre:{
				required:true,
			},
			apellido:{
				required:true,
			},
			frecuencia:{
				required:true,
				number:true,
			},
		},
	});
	
});
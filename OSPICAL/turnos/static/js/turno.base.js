DEFAULT_MESSAGE = "Seleccionar";
MESSAGE_NO_ESPECIALISTAS_TITLE = "Sin especialistas";
MESSAGE_NO_ESPECIALISTAS_DESCRIPCION = "No hay especialistas para esta especialidad";
MESSAGE_NO_DIAS = "El especialista no posee días disponibles para reservar turnos";
MESSAGE_NO_TURNOS = "No hay turnos disponibles este día";
MESSAGE_TURNO_YA_AGREGADO = "Ya agregó este turno";
MESSAGE_TURNO_NO_SELECCIONADO = "Debe seleccionar un turno para agregar";
MESSAGE_DNI_DUPLICADO_TITLE = "DNI duplicado";
MESSAGE_DNI_DUPLICADO_DESCRIPCION = "Deberá ingresar el número de afiliado para realizar la reserva";
MESSAGE_DNI_INEXISTENTE_TITLE = "DNI Inexistente";
MESSAGE_DNI_INEXISTENTE_DESCRIPCION = "Verifique que el número de DNI ingresado sea correcto";
MESSAGE_NUMERO_DUPLICADO_TITLE = "Número de afiliado duplicado";
MESSAGE_NUMERO_DUPLICADO_DESCRIPCION = "El número de afiliado está duplicado. Verifique los registros de base de datos de afiliados";
MESSAGE_NUMERO_INEXISTENTE_TITLE = "Número de afiliado Inexistente";
MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION = "Verifique que el número de número de afiliado ingresado sea correcto";
MESSAGE_ID_DUPLICADO_TITLE = "Identificador de afiliado duplicado";
MESSAGE_ID_DUPLICADO_DESCRIPCION = "El identificador de usuario está duplicado. Verifique los registros de base de datos de afiliados";
MESSAGE_ID_INEXISTENTE_TITLE = "Identificador de usuario inexistente";
MESSAGE_ID_INEXISTENTE_DESCRIPCION = "Identificador de usuario inexistente";
MESSAGE_SIN_TURNOS_RESERVADOS_HOY = "El afiliado no posee turnos reservados para hoy, o los mismos ya fueron considerados como ausente"
MESSAGE_SIN_TURNOS_RESERVADOS_HOY_TITLE= "No se encuentran turnos reservados para hoy"
MESSAGE_PRESENTISMO = "El afiliado ha faltado a muchos turnos en los ultimos meses";
MESSAGES_NO_ASIGNADO = "No asignado";
MESSAGE_RESERVAS = "Hay {0} turnos reservados";
MESSAGE_NO_RESERVAS = "No hay turnos reservados para este día";
DIA=["Domingo", "Lunes", "Martes", "Miércoles", "Jueves","Viernes","Sábado"];
MES=["enero", "febrero","marzo", "abril","mayo", "junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];	
ESTADOS={C:"Completo",S:"Sobreturno",X:"Cancelado"};


//////////////////////////////////////////////////////////////////////////////////
/**
 * Permite formatear una cadena como en C# mediante ubicadores posicionales
 * {0}{1}
 */
String.prototype.format = function () {
    var literal = this;
    if(arguments[0] instanceof Object) {
    	var object = arguments[0];
    	for (var i in object) {
	        var regex = new RegExp('\\{' + i + '\\}', 'g');
	        literal = literal.replace(regex, object[i]);
	    }
    } else {
	    for (var i = 0; i < arguments.length; i++) {
	        var regex = new RegExp('\\{' + i + '\\}', 'g');
	        literal = literal.replace(regex, arguments[i]);
	    }
    }
    return literal;
};
/**
 * Devuelve el numero con 2 digitos significativos
 * 
 * @param n
 *            Numero a convertir
 */
function n(n){
    return n > 9 ? n: "0" + n;
}

function mostrarMensaje(mensaje,options) {
	if(options && options.element) {
		options.element.addClass('error');
		options.element.attr({'title':mensaje});
	}
	title = options && options.title ? options.title : "";
	text = "<div><h1>{0}</h1><p>{1}</p></div>".format(title, mensaje);
	tipo = options && options.type ? options.type : "error";
	noty({text: text, type:tipo, layout:'bottom'});
}

////////////////////////////////////////////////////////////////////////////////////
function Lista(contenedor, options) {
	/** Este atributo hace referencia a un objecto del DOM que almacenará los
	 * ID de los objetos seleccionados */
	this.container = contenedor;
	this.listContainer = options && options.listContainer ? 
						 options.listContainer : 
					     $('#list-container');
	this.template = options && options.template ? 
					options.template : 
					this.__getTemplate();
	this.load();
	/* Si existen objetos cargados en la lista, llama a una funcion 
	 * para que los reconstruya y los muestre en el DOM */
	if(this.objects.length > 0 && typeof(options.rebuild) !== 'undefined')
		options.rebuild(this.objects);
}

/**
 * Obtiene la lista de objetos
 */
Lista.prototype.load = function(){
	var json = this.container.val(); // Reconstruyendo JSON
	this.objects = json ? eval(json) : new Array();
	return this.objects;
}

/**
 * Obtiene un template para crear una fila de la tabla
 */
Lista.prototype.__getTemplate = function() {
	var template = $.ajax({
			url:"/static/js/templates/generic.template.html",
			async: false});
	return template.responseText;
}

/**
 * Guarda la lista de objetos
 * 
 * @param turnos
 *            Lista de turnos a guardar
 */
Lista.prototype.save = function (){
	var json = JSON.stringify(this.objects);// Creando JSON
	this.container.val(json);
}

/**
 * Agrega un objeto a la lista
 */
Lista.prototype.add = function(obj) {
	if(this.objects.indexOf(obj.id) == -1) {
		this.objects.push(obj.id);
		this.save();
		this.addDOM(obj);
		return true;
	} else {
		return false;
	}
}

/**
 * Agrega un elemento al DOM
 */
Lista.prototype.addDOM = function(obj) {
	t = this.template.format(obj)
	this.listContainer.append(t);
	$('#rem-tr-{id}'.format(obj)).click(function(e) {
		e.preventDefault();
		var id = /rem-tr-(\d+)/i.exec(this.id)[1];
		$('#tr-{0}'.format(id)).remove();
		l.remove(id);
	})
}

/**
 * Elimina un elemento de la lista
 * 
 * @param id
 *            id del objeto a eliminar
 */
Lista.prototype.remove = function (id) {
	var index = this.objects.indexOf(id);
	this.objects.splice(index, 1);
	this.save();
}
//////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////
function Afiliado(obj) {
	if(obj) {
		this.id = obj.id;
		this.dni = obj.dni;
		this.numero = obj.numero;
		this.nombre = obj.nombre;
		this.apellido = obj.apellido;
		this.obtenerTelefono();
		this.verificarPresentismo();
		this.mostrar();
	}
}

/**
 * Obtiene el telefono del afiliado
 * @param afiliado
 *            id del afiliado
 */
Afiliado.prototype.obtenerTelefono = function () {
	var url = '/json/afiliado/id/{0}/telefono/'.format(this.id);
	$.getJSON(url, function(data) {
		if(data) {
			this.telefono = data[0];
			$("#id_telefono").val(this.telefono);
			$("#id_especialidad").focus();
		} else {
			$("#id_telefono").focus();
		}
	});
}

Afiliado.prototype.verificarPresentismo = function () {
	var url = '/json/presentismo/{0}/'.format(this.id);
	$.getJSON(url, function(data) {
		this.presentismo = data.presentismo_ok;
		if(!this.presentismo)
			mostrarMensaje(MESSAGE_PRESENTISMO, {type:'information'});
	});
}

Afiliado.prototype.mostrar = function () {
	$("#id_afiliado").val(this.id);
	$("#id_dni").val(this.dni);
	$("#id_numero").val(this.numero).mask('0000 0000 0000');
	$("#id_nombre").val(this.nombre);
	$("#id_apellido").val(this.apellido);
}

Afiliado.load = function(filter) {
	/*** Carga un afiliado, segun el filtro especificado
	 * El filtro trabaja con id, numero o dni***/
	var url = "";
	// Configuro la url y los mensajes de error, segun el filtro pasado
	if (filter.numero) {
		url = "/json/afiliado/numero/{0}/".format(filter.numero);
		duplicateError = {message:MESSAGE_NUMERO_DUPLICADO_DESCRIPCION,
						  title:MESSAGE_NUMERO_DUPLICADO_TITLE};
		notExistsError = {title:MESSAGE_NUMERO_INEXISTENTE_TITLE,
						  message:MESSAGE_NUMERO_INEXISTENTE_DESCRIPCION};
	} else if (filter.dni) {
		url = "/json/afiliado/dni/{0}/".format(filter.dni);
		duplicateError = {title:MESSAGE_DNI_DUPLICADO_TITLE,
				  		  message:MESSAGE_DNI_DUPLICADO_DESCRIPCION};
		notExistsError = {title:MESSAGE_DNI_INEXISTENTE_TITLE,
						  message:MESSAGE_DNI_INEXISTENTE_DESCRIPCION};
	} else if (filter.id) {
		url = "/json/afiliado/id/{0}/".format(filter.id);
		duplicateError = {title:MESSAGE_ID_DUPLICADO_TITLE,
		  		  		message:MESSAGE_ID_DUPLICADO_DESCRIPCION};
		notExistsError = {title:MESSAGE_ID_INEXISTENTE_TITLE,
						  message:MESSAGE_ID_INEXISTENTE_DESCRIPCION}
	}
	// Hago la llamada ajax para cargar el afiliado desde el servidor
	var af;
	if (url)
		$.ajax({
			url : url,
			dataType : 'json',
			async : false,
			success : function(data) {
				if (data.length == 1) {
					af = new Afiliado(data[0])
				} else if (data.length > 1) {
					mostrarMensaje(duplicateError.message, {
								   type : 'warning',
								   title : duplicateError.title});
				} else {
					mostrarMensaje(notExistsError.message, {
								   title : notExistsError.title});
				}
			},
		});
	return af;
}
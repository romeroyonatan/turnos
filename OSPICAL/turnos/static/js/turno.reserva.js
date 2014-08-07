// =============================================================================
// ListaDesplegable
// =============================================================================
ListaDesplegable = function() {
}

ListaDesplegable.prototype = {
    /**
     * Identificador del objeto
     */
    id: null,
    /**
     * contiene los elementos de la lista
     */
    elementos: [],
    
    /**
     * apunta al elemento seleccionado
     */
    seleccionado: null,
    
    /**
     * es el objeto dom que mostrara la lista en el navegador
     */
    dom: null,
    
    /**
     * apunto al mediador
     */
    mediador: null,
    
    /**
     * Constructor
     */
    init : function(dom) {
        this.id = Math.random();
        if (dom) {
            this.dom = dom;
            // establezco lo que debe hacer el objeto cuando el dom cambie de 
            // estado y le asigno el contexto para que this apunte a este objeto
            this.dom.change($.proxy(function() {
                this.seleccionado = this.dom.val();
                this.cambioEstado();
            }, this));
        }
    },
	
    /**
     * Este metodo sera llamado cada vez que cambie el estado del objeto dom
     */
    cambioEstado: function() {
        // notifico al mediador que cambie mi estado
        this.mediador.notificar(this);
    },
    
    /**
     * Obtiene los elementos que compondran la lista desplegable a traves de 
     * ajax y en formato JSON
     * 
     * @param url: (opcional) url donde se buscara la lista de objetos que 
     *             rellenaran la lista
     * @param error_mensaje: (opcional) mensaje de error en caso que la lista de 
     *                                  elementos este vacia
     * @param error_titulo: (opcional) titulo del mensaje de error
     */
    __obtenerElementos: function(url, error_mensaje, error_titulo) {
        if(url) {
            // obtengo la lista de especialista en formato JSON a traves de ajax
            $.getJSON(url, $.proxy(function(data) {
                // si existen elementos
                if(data.length > 0)
                    // cargo la lista de elementos
                    this.elementos = data;
                else
                    // si no hay elementos muestro un mensaje de error
                    if(error_mensaje)
                    mostrarMensaje(error_mensaje,
                                   {title:error_titulo});
            // establezco el contexto del objeto para que this apunte a esta 
            // objeto
            }, this));
        }
    },
	
    /**
     * Muestra los elementos en el objeto DOM
     */
	cargar: function() {},
	
	/**
	 * Selecciona un elemento de la lista. Si no se pasan argumentos selecciona
	 * al primero disponible
	 */
	seleccionar: function(index) {
	    // Si no se pasan argumentos selecciono el primero
	    var index = index | 0;
	    // valido que el elemento exista en el array
	    if (index>=0 && index < this.elementos.length) {
    	    // selecciono el elemento
    	    this.dom.prop('selectedIndex', index);
    	    //XXX: Ver si esto lo llama solo cuando seleccionamos el elemento 
    	    // en la linea anterior
    	    this.dom.change();
	    }
	},
	
	/**
	 * Desactiva el elemento DOM
	 */
	desactivar: function() {
	    this.dom.prop({disabled: true});
	},
	
	/**
	 * Activa el elemento DOM
	 */
	activar: function() {
	    this.dom.removeAttr('disabled');
	},
	
	/**
	 * Le da el foco al elemento del DOM
	 */
	foco: function() {
	    this.dom.focus();
	},
	
    /**
     * Vacia la lista de elementos
     * 
     */
    vaciar: function() {
        this.elementos = [];
        this.dom.empty();
    },
};


// =============================================================================
// Especialidades
// =============================================================================
Especialidades = function() {
};
Especialidades.prototype = new ListaDesplegable;

// =============================================================================
// Especialistas
// =============================================================================
Especialistas = function(dom) {
};
Especialistas.prototype = new ListaDesplegable;

/**
 * Obtiene los elementos que compondran la lista desplegable
 */
Especialistas.prototype.obtenerElementos = function(especialidad) {
    if (especialidad) {
        // configuro los parametros para buscar los elementos de la lista
        var url = '/json/especialistas/especialidad/{0}/'.format(especialidad);
        var error_mensaje = MESSAGE_NO_ESPECIALISTAS_DESCRIPCION;
        var error_titulo = MESSAGE_NO_ESPECIALISTAS_TITLE;
        // obtengo la lista de elementos
        this.__obtenerElementos(url, error_mensaje, error_titulo);
    }
}

/**
 * Muestra los elementos en el objeto DOM
 */
Especialistas.prototype.cargar = function(especialidad) {
    var options = "";
    // cargo los elementos de la lista
    this.obtenerElementos(especialidad)
    // Recorro la lista de elementos
    $.each(this.elementos, function(index, value) {
        // creo el elemento de la lista 
        options += '<option value="{0}">{1}, {2}</option>'.format(value.id,
                                                                 value.apellido,
                                                                 value.nombre);
    });
    // agrego los elementos a la lista desplegable
    this.dom.empty().append(options);
}

// =============================================================================
// Dias
// =============================================================================
Dias = function() {
};
Dias.prototype = new ListaDesplegable;

/**
 * Obtiene los elementos que compondran la lista desplegable
 */
Dias.prototype.obtenerElementos = function(especialista) {
    if (especialista) {
        // configuro los parametros para buscar los elementos de la lista
        var url = '/json/turnos/{0}/'.format(especialista);
        var error_mensaje = MESSAGE_NO_DIAS;
        // obtengo la lista de elementos
        this.__obtenerElementos(url, error_mensaje);
    }
}

/**
 * Muestra los elementos en el objeto DOM.
 * 
 * Selecciona el primer turno disponible
 */
Dias.prototype.cargar = function(especialista) {
    // cargo los elementos de la lista
    this.obtenerElementos(especialista)
    // para almacenar las opciones del menu
    var options = "";
    // para seleccionar el primer dia disponible
    var disponible = -1;
    
    // Recorro la lista de elementos
    $.each(this.elementos, function(index, value) {
        // obtengo la descripcion del estado del dia (completo, con 
        // sobreturnos, etc)
        var estado = ESTADOS[value.estado] ? 
                     "["+ESTADOS[value.estado]+"] " : "";
        // creo un nuevo objeto del tipo Date a partir de milisegundos
        var milis = value.fecha * 1000;
        var fecha = new Date(milis);
        // creo el elemento de la lista 
        options += '<option value="{0}">{4}{1}, {2} de {3}</option>'.format(
                milis, 
                DIA[fecha.getDay()],
                fecha.getDate(),
                MES[fecha.getMonth()],
                estado);
        // busco el primer dia que posea turnos disponibles
        if (disponible == -1 && value.estado === null)
            disponible = index; 
    });
    
    // agrego los elementos a la lista desplegable
    this.dom.empty().append(options);
    // selecciono el primer turno disponible
    this.seleccionar(disponible)
}

// =============================================================================
// TurnosDisponibles
// =============================================================================
TurnosDisponibles = function() {
};
TurnosDisponibles.prototype = new ListaDesplegable;

/**
 * Obtiene los elementos que compondran la lista desplegable.
 */
TurnosDisponibles.prototype.obtenerElementos = function(especialista, milis) {
    if (especialista && milis) {
        // configuro los parametros para buscar los elementos de la lista
        var d = new Date(parseInt(milis));
        var url = '/json/turnos/{0}/{1}/{2}/{3}/'.format(especialista, 
                                                          d.getFullYear(),
                                                          d.getMonth() + 1,
                                                          d.getDate());
        var error_mensaje = MESSAGE_NO_TURNOS;
        // obtengo la lista de elementos
        this.__obtenerElementos(url, error_mensaje);
    }
}

/**
 * Muestra los elementos en el objeto DOM
 */
TurnosDisponibles.prototype.cargar = function(especialista, dia) {
    var options = "";
    // cargo los elementos de la lista
    this.obtenerElementos(especialista, dia)
    // Recorro la lista de elementos
    $.each(this.elementos, function(index, value) {
        // creo el elemento de la lista 
        var fecha = new Date(value.fecha * 1000)
        options += '<option value="{0}">{1}:{2}</option>'.format(
                    value.id, 
                    n(fecha.getHours()),
                    n(fecha.getMinutes()));
    });
    // agrego los elementos a la lista desplegable
    this.dom.empty().append(options);
}


// =============================================================================
// DNI
// =============================================================================
DNI = function() {
};
DNI.prototype = new ListaDesplegable;

/**
 * Constructor
 */
DNI.prototype.init = function(dom) {
    ListaDesplegable.prototype.init();
    this.dom = dom;
    // defino el evento blur para que notifique el cambio de estado
    this.dom.blur($.proxy(function() {
        this.cambioEstado();
    }, this));
}


/**
* Obtiene los elementos que compondran la lista desplegable.
*/
DNI.prototype.obtenerElementos = function() {
    // obtengo el dni a buscar
    var dni = this.dom.val();
    // si el dni esta cargado
    if(/^\d+$/.test(dni))
        Afiliado.load({dni:dni});
}

/**
* Muestra los elementos en el objeto DOM
*/
DNI.prototype.cargar = function() {
    this.obtenerElementos();
}


// =============================================================================
// NumeroAfiliado
// =============================================================================
NumeroAfiliado = function() {
};
NumeroAfiliado.prototype = new DNI;

/**
* Obtiene los elementos que compondran la lista desplegable.
*/
NumeroAfiliado.prototype.obtenerElementos = function() {
 // obtengo el numero de afiliado a buscar
 var numero_afiliado = this.dom.data('mask').getCleanVal();
 // si el numero de afiliado esta cargado
 if(/^\d+$/.test(numero_afiliado))
     Afiliado.load({numero:numero_afiliado});
}

// =============================================================================
// Mediador
// =============================================================================
Mediador = function(){
    // creo los colegas
	this.especialidades = new Especialidades();
	this.especialistas = new Especialistas();
	this.dias = new Dias();
	this.turnos_disponibles = new TurnosDisponibles();
	this.dni = new DNI();
	this.numero_afiliado = new NumeroAfiliado();
	
	// asocio los colegas con el mediador
	this.especialidades.mediador = this;
    this.especialistas.mediador = this; 
    this.dias.mediador = this;
    this.turnos_disponibles.mediador = this;
    this.dni.mediador = this;
    this.numero_afiliado.mediador = this;
    
    // declaro array de metodos
    this.metodos = new Array();
};
Mediador.prototype = {
    /**
     * Constructor
     */
	init: function() {
	    // desactivo los especialistas, dias y turnos disponibles
		this.especialistas.desactivar();
		this.dias.desactivar();
		this.turnos_disponibles.desactivar();
		
		// muestro las especialidades
	    this.especialidades.cargar();

	    // asocio que metodo se ejecutara cuando cambie de estado el objeto(key)
	    this.metodos[this.especialidades.id] = this.cambiaEspecialidad;
	    this.metodos[this.especialistas.id] = this.cambiaEspecialista;
	    this.metodos[this.dias.id] = this.cambiaDia;
	    this.metodos[this.dni.id] = this.cambiaAfiliado;
	    this.metodos[this.numero_afiliado.id] = this.cambiaAfiliado;
	    
	    // configuro el ajax
	    $.ajaxSetup({
	        async: false,
	    });
	},
	
	/**
	 * Este metodo es llamado cada vez que un objeto observado cambia de estado
	 */
	notificar: function(obj) {
	    // selecciono el metodo a ejecutar en base al objeto que se modifico
	    metodo = this.metodos[obj.id];
	    // ejecuto el metodo con el contexto del objeto mediador
	    if (metodo)
	        $.proxy(metodo, this)(obj);
	},
	
	/*
     * Define la plantilla de como se comunicaran los objetos ListaDesplegable.
     * Patron TemplateMethod
     */
	__templateCargar: function(origen, destino){
        // vacio el contenido del destino
	    destino.vaciar();
	    // cargo los objetos en base al objeto seleccionado del origen
        destino.cargar(origen.seleccionado);
        // si hay elementos en el destino
        if (destino.elementos.length) {
            // activo el destino
            destino.activar();
            destino.foco();
            // si hay un solo elemento del campo destino, lo selecciono
            if (destino.elementos.length == 1)
                destino.seleccionar();
        }
	},
	
	/**
     * Este metodo es llamado cada vez que cambia una especialidad
     */
	cambiaEspecialidad: function() {
	    // desactivo la casilla de dias y turnos disponibles
	    this.especialistas.desactivar();
	    this.dias.desactivar();
	    this.turnos_disponibles.desactivar();
	    // cargo los especialistas
	    this.__templateCargar(this.especialidades, this.especialistas);
	},
	
	/**
     * Este metodo es llamado cada vez que cambia un especialista
     */
	cambiaEspecialista: function() {
        // desactivo la casilla de turnos disponibles
        this.dias.desactivar();
        this.turnos_disponibles.desactivar();
        // cargo los dias que atiende el especialista
        this.__templateCargar(this.especialistas, this.dias);
    },
    
    /**
     * Este metodo es llamado cada vez que cambia un dia
     */
	cambiaDia: function() {
        // desactivo la casilla de turnos disponibles
        this.turnos_disponibles.desactivar();
        // cargo los dias que atiende el especialista
        // cargo los turnos disponibles del especialista y para el dia 
	    // seleccionado
        this.turnos_disponibles.cargar(this.especialistas.seleccionado,
                                       this.dias.seleccionado);
        // activo el campo de turnos disponibles
        this.turnos_disponibles.activar();
        this.turnos_disponibles.foco();
        // selecciono el primer turno disponible
        this.turnos_disponibles.seleccionar();
	},
	
	/**
	 * este metodo es llamado cada vez que cambia un afiliado
	 */
	cambiaAfiliado: function(obj) {
       obj.cargar();
	},
	
	/**
	 * Este metodo cambia cada vez que se agrega un turno
	 */
	agregarTurno: function() {},
}

$(document).ready(function(){
	// creo y configuro el mediador
	var mediador = new Mediador();
	mediador.especialidades.init($("#id_especialidad"));
    mediador.especialistas.init($("#id_especialista"));
    mediador.dias.init($("#id_dia"));
    mediador.turnos_disponibles.init($("#id_hora"));
	mediador.dni.init($('#id_dni'));
	mediador.numero_afiliado.init($('#id_numero'))
	mediador.init();

	// defino lo que hace el boton reset
	$(':reset').click(function(){
		$('#tabla_turnos > tbody > tr').remove();
		$('#id_turnos, #id_afiliado').val('');
		$("#id_especialista, #id_dia, #id_hora").prop({disabled: true});
	});
	
	// defino lo que hace el campo dni y numero cuando apreto enter
	$("#id_dni, #id_numero").keypress(function(e) {
		// tecla enter
	    if(e.which == 13) {
	    	e.preventDefault() // desactivo la funcionalidad por defecto
	    	$("#id_telefono").focus(); // doy foco en el telefono
	    }
	});
	
	// defino las tareas a realizar antes de enviar el formulario
    $('form').submit(function() {
        $('#id_dni').number(true,0,'','');
        $('#id_numero').unmask();
    });
	
	// configuro las mascaras de los input
	$('#id_dni').number(true, 0,',','.');
	$('#id_numero').mask('0000 0000 0000');
	
	// defino las reglas de validacion
	$('form').validate({
		errorElement:'span',
		errorClass:'error triangle-right left',
		rules: {
			numero: "required",
			dni: "required",
			telefono: "required",
		},
		messages: {
			numero: "Debe ingresar el número de afiliado",
			dni: "Debe ingresar el DNI",
			telefono: "Debe ingresar un telefono",
		}
	});
	$('form').each (function(){
	    this.reset();
	});
});
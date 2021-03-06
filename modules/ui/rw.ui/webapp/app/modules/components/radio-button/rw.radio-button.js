
/*
 * 
 * (c) Copyright RIFT.io, 2013-2016, All Rights Reserved
 *
 */

var React = require('react');
var ButtonEventListenerMixin = require('../mixins/ButtonEventListener.js');


/**
 *  A radio-button component.
 *  It's props values and a brief description below
 *
 *  label:        The label for the radio button group.
 *  radiobuttons: The object that creates each radio button.  Each object has a property "label" and "checked".
 *    label:        The label for the individual radio button.
 *    checked:      If set to true, the individual radio button is initialized with a check.
 *  requiredText: The text content of the "if required" message.
 *  errorText:    The text content of the error message.
 *  ClassName:    Css Classes applied to the element.
 *  size:         The size of the element.
 *  isRequired:   A boolean indicating whether or not the input is required.
 *  isDisabled:   A boolean indicating the disabled state of the element.
 *  isReadOnly:   A boolean indicating whether or not the input is read only.
 *  instructions: The text content of the instructions
 **/
module.exports = React.createClass({
  displayName: "RadioButton",
  mixins:[ButtonEventListenerMixin],
  propTypes: {
    name:            React.PropTypes.string,
    label:           React.PropTypes.string,
    radiobuttons:    React.PropTypes.arrayOf(
      React.PropTypes.shape(
        {
          label:   React.PropTypes.string,
          checked: React.PropTypes.bool
        }
      )),
    requiredText:    React.PropTypes.string,
    errorText:       React.PropTypes.string,
    placeholder:     React.PropTypes.string,
    className:       React.PropTypes.string,
    size:            React.PropTypes.string,
    isRequired:      React.PropTypes.bool,
    isDisabled:      React.PropTypes.bool,
    isReadOnly:      React.PropTypes.bool,
    instructions:    React.PropTypes.string
  },


  /**
   * Sets the default input state.
   * If there is no description for the variable, assume it's the same as it's props counterpart.
   *
   * isActive: Boolean to indicate if input is active.
   * isHovered: Boolean to indicate if the input is being hovered over.
   * isFocused: Boolean to indicate if the input has been focused.
   * isDisabled: Boolean to indicate if input has been disabled.
   *
   * @returns {{sizeOfButton: (*|string), isActive: boolean, isHovered: boolean, isFocused: boolean, isDisabled: (*|boolean),
   * isReadOnly: (*|.textInput.isReadOnly|.exports.propTypes.isReadOnly|.exports.getInitialState.isReadOnly|boolean),
   * isRequired: (*|.textInput.isRequired|.exports.propTypes.isRequired|.exports.getInitialState.isRequired|isRequired|null),
   * isValid: null, isSuccess: null}}
   */
  getInitialState: function() {
    return {
      label:            this.props.label || "",
      requiredText:     this.props.requiredText || "Required",
      instructionsText: this.props.instructions || "",
      errorText:        this.props.errorText || "",
      size:             this.props.size || '',
      isActive:         false,
      isHovered:        false,
      isFocused:        false,
      isDisabled:       this.props.disabled || false,
      isReadOnly:       this.props.isReadOnly || false,
      isRequired:       this.props.isRequired || null,
      isValid:          null,      // Three way bool. Valid: true.   Invalid: false. Not acted on: null.
      isSuccess:        null       // Three way bool. Success: true. Error: false.   Not acted on: null.
    }
  },

  /**
   * If any of the state variables have changed, the component should update.
   * "nextProps" and "nextState" hold the state and property variables as they will be after the update.
   * "this.props" and "this.state" hold the state and property variables as they were before the update.
   * returns true if the state have changed. Otherwise returns false.
   * @param nextProps
   * @param nextState
   * @returns {boolean}
   */
  shouldComponentUpdate: function(nextProps, nextState) {
    var currentStateString = this.state.isReadOnly + this.state.isDisabled + this.state.isActive + this.state.isFocused +
      this.state.isHovered + this.state.isValid + this.state.isSuccess;
    var nextStateString = nextState.isReadOnly + nextState.isDisabled + nextState.isActive + nextState.isFocused +
      nextState.isHovered + nextState.isValid + nextState.isSuccess;
    if (currentStateString == nextStateString) {
      return false;
    }
    return true;
  },



  /**
   * Returns a string reflecting the current state of the input.
   * If the component state "isDisabled" is true, returns a string "disabled".
   * If the component state "isReadOnly" is true, returns a string "readonly".
   * Otherwise returns a string containing a word for each state that has been set to true.
   * (ie "active focused" if the states active and focused are true, but hovered is false).
   * @returns {string}
   */
  setComponentState: function() {
    var ret = "";
    if (this.state.isDisabled) {
      return "disabled";
    }
    if (this.state.isReadOnly) {
      return "readonly";
    }
    if (this.state.isActive) {
      ret += "active ";
    }
    if (this.state.isHovered) {
      ret += "hovered ";
    }
    if (this.state.isFocused) {
      ret += "focused ";
    }
    return ret;
  },

  /**
   * Renders the Text Input component.
   *
   **/
  render: function() {
    var input = [];
    var label = [];
    var input_style = {};
    var input_state = this.setComponentState();

    // The following if statements translates the min/max width from a number into a string.
    if (this.props.minWidth) {
      input_style['min-width'] = String(this.props.minWidth) + 'px';
    }
    if (this.props.maxWidth) {
      input_style['max-width'] = String(this.props.maxWidth) + 'px';
    }

    //// The input element.
    //input = React.createElement("input", {
    //    ref:               "inputRef",
    //    "data-state":      input_state,
    //    "type":            "checkbox",
    //    placeholder:       this.props.placeholder,
    //    pattern:           this.props.pattern,
    //    maxLength:         this.props.maxLength,
    //    required:          this.state.isRequired,
    //    disabled:          this.state.isDisabled,
    //    readOnly:          this.state.isReadOnly,
    //    onChange:          this.handleChange,
    //    onClick:           this.onClick,
    //    onMouseUp:         this.onMouseUp,
    //    onMouseDown:       this.onMouseDown,
    //    onMouseOver:       this.onMouseOver,
    //    onMouseEnter:      this.onMouseEnter,
    //    onMouseLeave:      this.onMouseLeave,
    //    onMouseOut:        this.onMouseOut,
    //    onTouchCancel:     this.onTouchCancel,
    //    onTouchEnd:        this.onTouchEnd,
    //    onTouchMove:       this.onTouchMove,
    //    onTouchStart:      this.onTouchStart,
    //    onKeyDown:         this.onKeyDown,
    //    onKeyPress:        this.onKeyPress,
    //    onKeyUp:           this.onKeyUp,
    //    onFocus:           this.onFocus,
    //    onBlur:            this.onBlur,
    //    className:         (this.props.className || "rw-textinput"),
    //    tabIndex:          0
    //  },
    //  null
    //);

    label = React.createElement("label", null, this.props.label);

    for (var i = 0; i < this.props.radiobuttons.length; i++) {

      // Label for the whole radio button group
      input[i] = React.createElement("label",
        {
          key:i*2 + 1,
          readOnly:this.props.readonly,
          disabled:this.props.disabled
        },

        // Creates each radio button input element.
        React.createElement("input", {
            key: i*2,
            defaultChecked: this.props.radiobuttons[i].checked,
            type: "radio",
            name: this.props.name,
            readOnly: this.props.readonly,
            disabled: this.props.disabled,
            onClick:           this.onClick,
            onMouseUp:         this.onMouseUp,
            onMouseDown:       this.onMouseDown,
            onMouseOver:       this.onMouseOver,
            onMouseEnter:      this.onMouseEnter,
            onMouseLeave:      this.onMouseLeave,
            onMouseOut:        this.onMouseOut,
            onTouchCancel:     this.onTouchCancel,
            onTouchEnd:        this.onTouchEnd,
            onTouchMove:       this.onTouchMove,
            onTouchStart:      this.onTouchStart,
            onKeyDown:         this.onKeyDown,
            onKeyPress:        this.onKeyPress,
            onKeyUp:           this.onKeyUp,
            onFocus:           this.onFocus,
            onBlur:            this.onBlur
          },
          null
        ),
        this.props.radiobuttons[i].label);
    }

    // The "if required" element. It displays a label if the element is required.
    if(this.props.isRequired == true){
      var requiredEle = React.createElement("small", {className: "rw-form-requiredLabel"}, this.state.requiredText);
    }

    // The "error" element.  It pops up as a message if there is an error with the input.
    if(this.state.errorText != "") {
      var error = React.createElement("p", {className: "rw-form-errorMsg"}, this.state.errorText);
    }

    // The "instruction" element.
    if(this.state.instructionsText != ""){
      var instructions = React.createElement("p", {className: "rw-form-instructions"}, this.state.instructionsText)
    }

    // The parent element for all.
    var ret = React.createElement("div", {
      "data-state":      input_state,
      required:          this.state.isRequired,
      disabled:          this.state.isDisabled,
      readOnly:          this.state.isReadOnly
    }, requiredEle, label, input, error, instructions);

    return ret;
  }
});

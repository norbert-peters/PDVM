import React from 'react';
import { PdvmTextFieldText } from '../../pdvmComponents/PdvmTextField/styles';
import { PdvmTextField } from '../../pdvmComponents/PdvmTextField/';
import { StyledPdvmTextField, FormRow } from './styles';
class PdvmForm extends React.Component {
  state = {
    values: {
      field1: "Yeah I am a reusable component!",
      field2: ""
    }
  }
 onChange = event => {
    const newValuesObj = Object.assign({}, this.state.values, {[event.target.name]: event.target.value});
    this.setState({
      values: newValuesObj
    });
  }
  render() {
    return (
      <React.Fragment>
        <FormRow>
          <PdvmTextField
            name="field1"
            type="text"
            value={this.state.values.field1}
            placeholder="Sexy Controlled Text Field"
            onChange={this.onChange}
          />
          <PdvmTextFieldText>
            <span>New Value: </span>
            <span>{this.state.values.field1}</span>
          </PdvmTextFieldText>
        </FormRow>
        <FormRow>
          <PdvmTextField
            name="field2"
            type="text"
            value={this.state.values.field2}
            placeholder="I have an error!"
            hasError="This is a required field!"
            onChange={this.onChange}
            isTouched
          />
        </FormRow>
        <FormRow>
          <StyledPdvmTextField
            name="field3"
            type="text"
            placeholder="I know I am special yeahhhh baby"
          />
        </FormRow>
      </React.Fragment>
    )
  }
}
export {
  PdvmForm
};

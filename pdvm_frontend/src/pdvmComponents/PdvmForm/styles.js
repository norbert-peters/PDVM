import styled from 'styled-components';
import { PdvmTextField } from '../../pdvmComponents/PdvmTextField/';
const StyledPdvmTextField = styled(PdvmTextField)`
  border-width: 2px;
  border-style: dashed;
  border-color: #1166ff;
  box-shadow: 0 4px 4px #1166ff;
  outline: none;
`
const FormRow = styled.div`
  width: 500px;
  margin: 20px auto;
`
export {
  StyledPdvmTextField,
  FormRow
};
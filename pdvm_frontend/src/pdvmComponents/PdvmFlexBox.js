import styled from 'styled-components'
import { Grid } from '../pdvmComponents/PdvmRaster';


export const PdvmFlexBox = styled(Grid)`
${({ theme }) => `
  color: ${theme.primaryDark}} ;
  background-color: ${theme.primaryLight} ;
  box-shadow: 5px 5px 3px #888888;
  margin-bottom: 0.5em;
​​  `}
`;

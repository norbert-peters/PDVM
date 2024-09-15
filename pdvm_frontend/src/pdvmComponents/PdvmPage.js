import styled from 'styled-components';
import { device, maxSize } from './PdvmDevice';

export const PdvmPage = styled.div`
${({ theme }) => `
  margin: auto;
  font-family: ${theme.typography.fontFamily};
  font-size: ${theme.typography.fontSize};
  text-align: center;
  background: ${theme.back.default};
  color: ${theme.front.default};

  @media ${device.mobileS} { 
    ${maxSize.mobileS};
  }

  @media ${device.mobileM} { 
    ${maxSize.mobileM};
  }

  @media ${device.mobileL} { 
    ${maxSize.mobileL};
  }

  @media ${device.tablet} { 
    ${maxSize.tablet};
  }

  @media ${device.laptop} { 
    ${maxSize.laptop};
  }

  @media ${device.laptopL} { 
    ${maxSize.laptopL};
  }

  @media ${device.desktop} { 
    ${maxSize.desktop};
  }
 
  `}
`;
